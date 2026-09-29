#!/usr/bin/env python3
"""Re-transcribe held PYQ rows from a per-question PDF crop.

Uses gemma4 + glm5.3-flash on the crop (not the full page). Resume from
out-math/agents/chapter_N/repair/. Does not overwrite auto_ok/human_ok.

    python repair_held_pyq.py --book math --chapter 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.figures_check import http_get_status, missing_figure_gets, upload_chapter_figures
from agents.katex_check import is_solver_dump
from agents.models import FALLBACK_SOLVERS, PRIMARY_SOLVER, TIEBREAK_MODEL, VISION_MODEL
from agents.promotion import final_publish_status
from agents.publish import shape_ok_for, upsert_question
from agents.solvers import solve_match, solver_has_answer
from format_ocr_math import format_ocr_math
from run_chapter_agents import (
    answer_for,
    row_audit_ok,
    row_katex_ok,
    solver_answer,
    spec_map,
    v2_json,
)

DPI = 200
PAD_PT = 6
CROP_SYSTEM = """You look at one printed JEE Main PYQ crop.
Return JSON only:
{"q_no":int,"mcq":bool,"body":str,"options":[str,str,str,str]|null}
Transcribe the printed stem and the four printed options (or options null for a numerical).
Use $...$ KaTeX for math. Paper-only: no solver talk, no book headings, no page numbers.
Keep [[fig:KEY]] if the crop includes that token in the prompt."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _same_column_later(spec: dict, specs: dict[int, dict]) -> list[dict]:
    y0 = spec["bbox"][1]
    return [
        s for s in specs.values()
        if s["page"] == spec["page"]
        and s.get("column") == spec.get("column")
        and s["bbox"][1] > y0 + 2
        and int(s["q_no"]) != int(spec["q_no"])
    ]


def _pixmap_clip(page, rect: pymupdf.Rect) -> pymupdf.Pixmap:
    clip = (rect + pymupdf.Rect(-PAD_PT, -PAD_PT, PAD_PT, PAD_PT)) & page.rect
    return page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip)


def _stitch_pixmaps(pixes: list[pymupdf.Pixmap], dest: Path) -> Path:
    w = max(p.width for p in pixes)
    h = sum(p.height for p in pixes)
    out = pymupdf.Pixmap(pixes[0].colorspace, pymupdf.IRect(0, 0, w, h), pixes[0].alpha)
    out.clear_with(255)
    y = 0
    for pix in pixes:
        src = pix
        if src.width < w or src.x != 0 or src.y != y:
            padded = pymupdf.Pixmap(
                src.colorspace, pymupdf.IRect(0, y, src.width, y + src.height), src.alpha
            )
            padded.clear_with(255)
            src.set_origin(0, y)
            padded.copy(src, src.irect)
            src = padded
        else:
            src.set_origin(0, y)
        out.copy(src, src.irect)
        y += pix.height
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(dest))
    return dest


def continuation_rect(doc: pymupdf.Document, spec: dict, specs: dict[int, dict]):
    """Options of the last item in a column often wrap to the next column / page."""
    if _same_column_later(spec, specs):
        return None
    page_no = int(spec["page"])
    col = spec.get("column")
    if col == "L":
        rights = [
            s for s in specs.values()
            if s["page"] == page_no and s.get("column") == "R"
        ]
        if not rights:
            return None
        first = min(rights, key=lambda s: s["bbox"][1])
        page = doc[page_no - 1]
        x0, _, x1, _ = first["bbox"]
        y1 = first["bbox"][1] - 2
        y0 = max(page.rect.y0 + 36, y1 - 90)
        if y1 - y0 < 16:
            return None
        return page_no, pymupdf.Rect(x0, y0, x1, y1)
    if col == "R":
        nxt_no = page_no + 1
        if nxt_no > doc.page_count:
            return None
        lefts = [
            s for s in specs.values()
            if s["page"] == nxt_no and s.get("column") == "L"
        ]
        nxt = doc[nxt_no - 1]
        if lefts:
            first = min(lefts, key=lambda s: s["bbox"][1])
            x0, _, x1, _ = first["bbox"]
            y1 = first["bbox"][1] - 2
        else:
            x0, x1 = 38.0, nxt.rect.width / 2
            y1 = min(nxt.rect.y0 + 220, nxt.rect.y1 - 8)
        y0 = nxt.rect.y0 + 36
        if y1 - y0 < 16:
            return None
        return nxt_no, pymupdf.Rect(x0, y0, x1, y1)
    return None


def crop_png(pdf: Path, spec: dict, dest: Path, specs: dict[int, dict]) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    page = doc[int(spec["page"]) - 1]
    x0, y0, x1, y1 = spec["bbox"]
    same = _same_column_later(spec, specs)
    if same:
        nxt = min(same, key=lambda s: s["bbox"][1])
        y1 = max(y1, nxt["bbox"][1] - 2)
    clip = pymupdf.Rect(x0, y0, x1, y1)
    pixes = [_pixmap_clip(page, clip)]
    cont = continuation_rect(doc, spec, specs)
    if cont is not None:
        cont_page_no, cont_rect = cont
        pixes.append(_pixmap_clip(doc[cont_page_no - 1], cont_rect))
        _stitch_pixmaps(pixes, dest)
    else:
        if not same:
            y1 = min(page.rect.y1 - 8, y1 + 90)
            clip = pymupdf.Rect(x0, y0, x1, y1)
            pixes = [_pixmap_clip(page, clip)]
        pixes[0].save(str(dest))
    doc.close()
    return dest


def observe_crop(png: Path, spec: dict, model: str, env: dict, limiter: p.RateLimiter) -> dict:
    figs = spec.get("figure_keys") or []
    text = (
        f"Question Q{spec['q_no']} ({spec['answer_type']}). "
        f"Figure keys allowed: {json.dumps(figs)}. "
        "Transcribe this one question. If the paper has (1)(2)(3)(4), fill options. "
        "If the paper has a blank ______, set mcq false and options null."
    )
    messages = [{"role": "system", "content": CROP_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    return v2_json(model, messages, env, limiter)


def paper_spec(spec: dict, entry: dict) -> dict:
    """Paper blanks are numericals even when the answer-key row was tagged mcq."""
    body = (entry.get("body") or "").strip()
    options = entry.get("options")
    has_opts = isinstance(options, list) and len(options) == 4
    blank = bool(re.search(r"_{3,}|\.{3,}|…|\\dots", body))
    count_stem = bool(re.search(
        r"(?:number of (?:distinct )?(?:real )?roots|number of (?:distinct )?solutions|"
        r"number of (?:integral )?solution|number of points)\b",
        body,
        re.I,
    )) and re.search(r"(?:\bis\s*$|equal to\s*$|equal to\s*[._…\\dots]*$)", body)
    if spec["answer_type"] == "mcq" and not has_opts and (
        blank or count_stem or re.search(r"(?:equal to:?|is:?)\s*$", body, re.I)
    ):
        out = dict(spec)
        out["answer_type"] = "numerical"
        return out
    return spec


def load_or_observe(path: Path, png: Path, spec: dict, model: str,
                    env: dict, limiter: p.RateLimiter, *, force: bool) -> dict:
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        data = observe_crop(png, spec, model, env, limiter)
    except Exception as exc:
        data = {"error": f"{type(exc).__name__}: {exc}"}
    dump(path, data)
    return data


def adopt_entry(raw: dict, spec: dict) -> dict:
    body = format_ocr_math(str(raw.get("body") or "").strip())
    options = raw.get("options")
    use = paper_spec(spec, {"body": body, "options": options})
    if use["answer_type"] == "mcq" and isinstance(options, list) and len(options) == 4:
        options = [format_ocr_math(str(t or "")) for t in options]
    else:
        options = None
    if spec.get("figure_keys"):
        for key in spec["figure_keys"]:
            token = f"[[fig:{key}]]"
            if token not in body:
                body = f"{body}\n\n{token}".strip()
    return {"body": body, "options": options, "page": spec["page"]}


def quality_ok(spec: dict, entry: dict) -> bool:
    body = entry.get("body") or ""
    spec = paper_spec(spec, entry)
    if is_solver_dump(body):
        return False
    if not shape_ok_for(spec, entry):
        return False
    if not row_audit_ok(entry):
        return False
    if len(body.strip()) < 40:
        return False
    if re.search(r"\\sqrt\{\s*\}|\^\{\.\.\.\}", body):
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--book", choices=sorted(p.BOOKS), default="math")
    args = ap.parse_args(argv)
    book = p.configure_book(args.book)
    env = p.load_env()
    limiter = p.RateLimiter(60)
    chapter_no = args.chapter
    specs = spec_map(p.load_skeleton(), chapter_no)
    if not specs:
        raise SystemExit(f"no skeleton rows for chapter {chapter_no}")
    out_dir = p.OUT / "agents" / f"chapter_{chapter_no}"
    repair_dir = out_dir / "repair"
    repair_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = out_dir / "parsed.json"
    parsed = json.loads(parsed_path.read_text(encoding="utf-8")) if parsed_path.exists() else {}
    key_book = p.load_answer_key()
    sb = p.supabase_client()
    ch_id = p.resolve_chapter_id(sb, chapter_no, book["subject_name"])
    q_rows = sb.table("pyq_questions").select("id,q_no,review_status").eq(
        "chapter_id", ch_id).execute().data
    q_ids = {int(r["q_no"]): r["id"] for r in q_rows}
    status = {int(r["q_no"]): r["review_status"] for r in q_rows}
    pdf = Path(book["pdf"])
    held = [q for q in sorted(specs) if status.get(q) not in ("auto_ok", "human_ok")]
    print(f"{args.book} chapter {chapter_no}: repair {len(held)} held / {len(specs)}", flush=True)
    fig_urls = upload_chapter_figures(chapter_no, sb)
    missing_figs = set(missing_figure_gets(fig_urls, http_get_status))
    if missing_figs:
        print(f"  figure GET fail {sorted(missing_figs)}", flush=True)
    promoted = 0
    still = 0
    for q_no in held:
        spec = specs[q_no]
        if any(k in missing_figs or k not in fig_urls for k in (spec.get("figure_keys") or [])):
            print(f"  q{q_no} figure GET fail", flush=True)
            still += 1
            continue
        crop = repair_dir / f"q{q_no:03d}.png"
        gemma_path = repair_dir / f"q{q_no:03d}_gemma.json"
        flash_path = repair_dir / f"q{q_no:03d}_flash.json"
        try:
            crop_png(pdf, spec, crop, specs)
        except Exception as exc:
            print(f"  q{q_no} crop fail {exc}", flush=True)
            still += 1
            continue
        print(f"  q{q_no} page {spec['page']}", flush=True)
        gemma = load_or_observe(
            gemma_path, crop, spec, VISION_MODEL, env, limiter, force=False
        )
        entry = adopt_entry(gemma, spec) if gemma.get("body") else None
        if entry is None or not quality_ok(spec, entry):
            gemma = load_or_observe(
                gemma_path, crop, spec, VISION_MODEL, env, limiter, force=True
            )
            entry = adopt_entry(gemma, spec) if gemma.get("body") else None
        vision_ok = False
        if entry is None or not quality_ok(spec, entry):
            flash = load_or_observe(
                flash_path, crop, spec, TIEBREAK_MODEL, env, limiter, force=False
            )
            flash_entry = adopt_entry(flash, spec) if flash.get("body") else None
            if flash_entry is None or not quality_ok(spec, flash_entry):
                flash = load_or_observe(
                    flash_path, crop, spec, TIEBREAK_MODEL, env, limiter, force=True
                )
                flash_entry = adopt_entry(flash, spec) if flash.get("body") else None
            if flash_entry is not None and quality_ok(spec, flash_entry):
                entry = flash_entry
                vision_ok = bool(gemma.get("body")) and quality_ok(
                    spec, adopt_entry(gemma, spec)
                )
            else:
                still += 1
                continue
        else:
            flash = load_or_observe(
                flash_path, crop, spec, TIEBREAK_MODEL, env, limiter, force=False
            )
            flash_entry = adopt_entry(flash, spec) if flash.get("body") else None
            if flash_entry is None or not quality_ok(spec, flash_entry):
                flash = load_or_observe(
                    flash_path, crop, spec, TIEBREAK_MODEL, env, limiter, force=True
                )
                flash_entry = adopt_entry(flash, spec) if flash.get("body") else None
            vision_ok = flash_entry is not None and quality_ok(spec, flash_entry)

        use_spec = paper_spec(spec, entry)
        if use_spec["answer_type"] != "mcq":
            entry["options"] = None
        try:
            katex_ok = row_katex_ok(entry, env, limiter)
        except Exception:
            katex_ok = False
        if (not katex_ok or not quality_ok(use_spec, entry)) and flash_path.exists():
            flash = json.loads(flash_path.read_text(encoding="utf-8"))
            flash_entry = adopt_entry(flash, spec) if flash.get("body") else None
            if flash_entry is not None and quality_ok(spec, flash_entry):
                try:
                    flash_katex = row_katex_ok(flash_entry, env, limiter)
                except Exception:
                    flash_katex = False
                if flash_katex:
                    entry = flash_entry
                    use_spec = paper_spec(spec, entry)
                    if use_spec["answer_type"] != "mcq":
                        entry["options"] = None
                    katex_ok = True
        if not katex_ok or not quality_ok(use_spec, entry):
            still += 1
            continue

        key_row = answer_for(key_book, chapter_no, q_no)
        match = False
        glm_ans = ds_ans = None
        if key_row is not None:
            try:
                glm_ans = solver_answer(PRIMARY_SOLVER, entry, use_spec, fig_urls, env, limiter)
            except Exception:
                glm_ans = None
            if solver_has_answer(str(glm_ans or ""), key_row["type"]):
                match = solve_match(str(glm_ans), "", key_row["type"], key_row["value"])
            else:
                for fallback in FALLBACK_SOLVERS:
                    try:
                        ds_ans = solver_answer(fallback, entry, use_spec, fig_urls, env, limiter)
                        break
                    except Exception:
                        ds_ans = None
                if solver_has_answer(str(ds_ans or ""), key_row["type"]):
                    match = solve_match("", str(ds_ans), key_row["type"], key_row["value"])
        confidence = 1.0 if vision_ok else 0.5
        gates = {
            "skeleton": True,
            "shape_ok": True,
            "coverage_ok": True,
            "vision_ok": vision_ok,
            "figures_ok": True,
            "audit_ok": True,
            "katex_ok": True,
            "solve_match": match,
            "confidence": confidence,
        }
        pub_status = final_publish_status(gates, entry.get("body") or "")
        if pub_status not in ("auto_ok", "human_ok"):
            still += 1
            continue
        answer = None if key_row is None else str(key_row["value"])
        written = False
        last_exc = None
        for attempt in range(5):
            try:
                upsert_question(
                    sb, q_ids[q_no], entry, pub_status,
                    1.0 if pub_status in ("auto_ok", "human_ok") else 0.5,
                    use_spec, answer=answer,
                )
                fmt = "mcq" if use_spec["answer_type"] == "mcq" else "numerical"
                sb.table("pyq_questions").update({"format": fmt}).eq(
                    "id", q_ids[q_no]
                ).execute()
                if fmt == "numerical":
                    sb.table("pyq_question_options").delete().eq(
                        "question_id", q_ids[q_no]
                    ).execute()
                written = True
                break
            except Exception as exc:
                last_exc = exc
                time.sleep(2 * (attempt + 1))
                sb = p.supabase_client()
        if not written:
            print(f"    upsert fail {last_exc}", flush=True)
            still += 1
            continue
        parsed[str(q_no)] = entry
        dump(parsed_path, parsed)
        promoted += 1
        print(f"    -> {pub_status}", flush=True)

    dump(parsed_path, parsed)
    print(f"repaired {promoted} still held {still}", flush=True)
    return 0 if still == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
