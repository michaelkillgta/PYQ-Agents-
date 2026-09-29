#!/usr/bin/env python3
"""Finish Mathematics PDF chapter 5 from OCR cache. No Gemini. No re-OCR."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from bakeoff import page_slice
from run_chapter_agents import (
    answer_for,
    chapter_dir,
    dump,
    observe_page,
    row_audit_ok,
    row_katex_ok,
    solver_answer,
    spec_map,
    tiebreak_page,
    write_hold_json,
)
from agents.figures_check import (
    chapter_figure_keys,
    http_get_status,
    missing_figure_gets,
    upload_chapter_figures,
)
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import SOLVER_A, SOLVER_B
from agents.promotion import final_publish_status
from agents.publish import shape_ok_for, upsert_question
from agents.report import build_report
from agents.solvers import solve_match
from agents.vision import observer_shape, question_rows, vision_agree

CHAPTER_NO = 5
BOOK = "math"
FIG_XREF = 375
FIG_PAGE = 46
JUNK_SOLVER = {"", "...", "?", "null", "none"}
HEADING_TAIL = re.compile(
    r"\s*(?:Permutation|Combination|Geometric Permutation|Factorial|"
    r"Selection of one or more items?|"
    r"Arrangement under Constraint|"
    r"Division and Distribution of Distinct(?: Objects)?|"
    r"Division of Identical items)\s*$",
    re.I,
)
OVERLAY = re.compile(r"\bmathongo\b|\bmathone\b|#\s*#\s*mi|\s+\d{1,3}(?:\s+\d{1,3})+\s+mi\b", re.I)
TRUNC_OPT = re.compile(r"^(√|N|\*|1/√|)$")


def _clean_field(text: str) -> str:
    s = HEADING_TAIL.sub("", text or "").strip()
    s = re.sub(r"\bmathone\b", " ", s, flags=re.I)
    s = re.sub(r"\bmathongo\b", " ", s, flags=re.I)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def clean_entry(entry: dict) -> dict:
    out = dict(entry)
    figs = re.findall(r"\[\[fig:[^\]]+\]\]", out.get("body") or "")
    out["body"] = _clean_field(out.get("body") or "")
    if figs and not any(f in (out["body"] or "") for f in figs):
        out["body"] = (out["body"] + "\n\n" + "\n".join(figs)).strip()
    opts = out.get("options")
    if isinstance(opts, list):
        out["options"] = [_clean_field(o) for o in opts]
    return out


def leftover_junk(entry: dict) -> str | None:
    fields = [entry.get("body") or ""]
    fields.extend(entry.get("options") or [])
    for t in fields:
        if OVERLAY.search(t or ""):
            return "overlay"
        if HEADING_TAIL.search(t or ""):
            return "truncated"
    opts = entry.get("options")
    if isinstance(opts, list):
        for o in opts:
            if TRUNC_OPT.fullmatch((o or "").strip()):
                return "truncated"
            if (o or "").rstrip().endswith("√") and len((o or "").strip()) <= 4:
                return "truncated"
    body = (entry.get("body") or "").strip()
    if body.endswith((" thi", " th", " the")):
        return "truncated"
    return None


def solver_missing(row: dict | None) -> bool:
    if not row:
        return True
    glm = str(row.get("glm") or "").strip()
    ds = str(row.get("deepseek") or "").strip()
    return glm.lower() in JUNK_SOLVER or ds.lower() in JUNK_SOLVER


def ensure_figure_png() -> Path:
    dest = p.OUT / "figures" / f"p{FIG_PAGE:03d}_x{FIG_XREF}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    doc = pymupdf.open(p.PDF_PATH)
    pix = pymupdf.Pixmap(doc, FIG_XREF)
    if pix.n - pix.alpha > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    pix.save(str(dest))
    doc.close()
    return dest


def rasterize_pages(pages: list[int]) -> None:
    pg_dir = p.OUT / "pages"
    pg_dir.mkdir(parents=True, exist_ok=True)
    missing = [n for n in pages if not (pg_dir / f"page_{n:03d}.png").exists()]
    if not missing:
        return
    doc = pymupdf.open(p.PDF_PATH)
    zoom = 200 / 72
    mat = pymupdf.Matrix(zoom, zoom)
    for n in missing:
        pix = doc[n - 1].get_pixmap(matrix=mat)
        pix.save(str(pg_dir / f"page_{n:03d}.png"))
    doc.close()


def main() -> int:
    book_spec = p.configure_book(BOOK)
    env = p.load_env()
    limiter = p.RateLimiter(40)
    skeleton_all = p.load_skeleton()
    specs = spec_map(skeleton_all, CHAPTER_NO)
    out_dir = chapter_dir(CHAPTER_NO)
    pages = sorted({r["page"] for r in specs.values()})
    print(f"math chapter {CHAPTER_NO}: {len(specs)} questions, pages {pages}", flush=True)

    ocr_dir = p.OUT / "ocr"
    missing_ocr = [n for n in pages if not (ocr_dir / f"page_{n:03d}.json").exists()]
    if missing_ocr:
        raise SystemExit(f"OCR cache miss; refusing re-OCR: {missing_ocr}")
    parsed_path = out_dir / "parsed.json"
    if not parsed_path.exists():
        raise SystemExit(f"missing {parsed_path}")
    raw_parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
    parsed = {int(k): clean_entry(v) for k, v in raw_parsed.items()}
    by_page: dict[int, list] = {}
    for q_no, entry in parsed.items():
        page_no = int(entry["page"])
        by_page.setdefault(page_no, []).append({
            "q_no": q_no,
            "body": entry.get("body"),
            "options": entry.get("options"),
        })
    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})

    ensure_figure_png()
    sb = p.supabase_client()
    fig_urls = upload_chapter_figures(CHAPTER_NO, sb)
    wanted_keys = chapter_figure_keys(skeleton_all, CHAPTER_NO)
    key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
    missing_figs = missing_figure_gets(key_to_url, http_get_status)
    if missing_figs:
        fig_urls = upload_chapter_figures(CHAPTER_NO, sb)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
    ok_fig_keys = {k for k in wanted_keys if k not in missing_figs}
    holds = [{"q_no": None, "reason": "figure_get", "figure_key": k, "decision": None}
             for k in missing_figs]

    gemma_path = out_dir / "gemma4.json"
    flash_path = out_dir / "glm53_flash.json"
    gemma_by_page = json.loads(gemma_path.read_text(encoding="utf-8")) if gemma_path.exists() else {}
    flash_by_page = json.loads(flash_path.read_text(encoding="utf-8")) if flash_path.exists() else {}
    need_vision = []
    for page_no in by_page:
        if not question_rows(gemma_by_page.get(str(page_no))):
            need_vision.append(page_no)
        cached_g = gemma_by_page.get(str(page_no))
        parse_obs = observer_shape(by_page[page_no], {s["q_no"]: s for s in page_slice(skeleton_all, page_no)})
        if question_rows(cached_g) and not vision_agree(parse_obs, cached_g):
            if not question_rows(flash_by_page.get(str(page_no))):
                need_vision.append(page_no)
    if need_vision:
        rasterize_pages(sorted(set(need_vision)))

    disagreements = []
    vision_ok_q = set()
    for page_no, questions in by_page.items():
        slice_ = page_slice(skeleton_all, page_no)
        spec_by_q = {s["q_no"]: s for s in slice_}
        parse_obs = observer_shape(questions, spec_by_q)
        print(f"vision page {page_no} ({len(questions)} q)", flush=True)
        cached = gemma_by_page.get(str(page_no))
        if question_rows(cached):
            gemma = cached
            print("  gemma4 cached", flush=True)
        else:
            gemma = observe_page(page_no, slice_, env, limiter)
            gemma_by_page[str(page_no)] = gemma
            dump(gemma_path, gemma_by_page)
        if vision_agree(parse_obs, gemma):
            vision_ok_q.update(int(q["q_no"]) for q in questions)
            continue
        disagreements.append({"page": page_no, "parse": parse_obs, "gemma": gemma})
        cached_flash = flash_by_page.get(str(page_no))
        if question_rows(cached_flash):
            flash = cached_flash
            print("  flash cached", flush=True)
        else:
            flash = tiebreak_page(page_no, slice_, env, limiter)
            flash_by_page[str(page_no)] = flash
            dump(flash_path, flash_by_page)
        if vision_agree(parse_obs, flash) or vision_agree(gemma, flash):
            vision_ok_q.update(int(q["q_no"]) for q in questions)
            continue
        for q in questions:
            holds.append({
                "q_no": int(q["q_no"]),
                "reason": "vision_conflict",
                "page": page_no,
                "decision": None,
            })
    dump(gemma_path, gemma_by_page)
    dump(flash_path, flash_by_page)
    dump(out_dir / "disagreements.json", disagreements)

    key_book = p.load_answer_key()
    solvers_path = out_dir / "solvers.json"
    solvers = json.loads(solvers_path.read_text(encoding="utf-8")) if solvers_path.exists() else {}
    ch_id = p.resolve_chapter_id(sb, CHAPTER_NO, book_spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    katex_log = {}
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no)
        if entry is None:
            holds.append({"q_no": q_no, "reason": "coverage_miss", "page": spec["page"], "decision": None})
            continue
        if q_no % 10 == 0 or q_no == 1:
            print(f"gates q {q_no}/{len(specs)}", flush=True)
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", entry.get("body") or "")
        figures_ok = all(k in ok_fig_keys for k in body_figs) and not any(
            h.get("figure_key") in body_figs for h in holds if h.get("reason") == "figure_get"
        )
        coverage_ok = True
        vision_ok = q_no in vision_ok_q
        shape_ok = shape_ok_for(spec, entry)
        junk = leftover_junk(entry)
        dump_ok = not is_solver_dump(entry.get("body") or "")
        audit_ok = row_audit_ok(entry) and junk is None
        try:
            katex_ok = row_katex_ok(entry, env, limiter)
        except Exception as exc:
            katex_ok = False
            katex_log[str(q_no)] = f"{type(exc).__name__}: {exc}"
        else:
            katex_log[str(q_no)] = katex_ok
        if not katex_ok:
            holds.append({"q_no": q_no, "reason": "katex_render", "decision": None})
        if not dump_ok:
            holds.append({"q_no": q_no, "reason": "solver_dump", "decision": None})
        if junk == "overlay":
            holds.append({"q_no": q_no, "reason": "overlay", "decision": None})
        elif junk == "truncated":
            holds.append({"q_no": q_no, "reason": "truncated", "decision": None})
        if not shape_ok:
            holds.append({"q_no": q_no, "reason": "shape", "decision": None})

        key_row = answer_for(key_book, CHAPTER_NO, q_no)
        prev = solvers.get(str(q_no)) or {}
        glm_ans = prev.get("glm")
        ds_ans = prev.get("deepseek")
        match = False
        if key_row is None:
            holds.append({"q_no": q_no, "reason": "solver_parse", "detail": "no answer_key row", "decision": None})
        else:
            try:
                if solver_missing(prev):
                    print(f"  retry solvers q {q_no}", flush=True)
                    glm_ans = solver_answer(SOLVER_A, entry, spec, fig_urls, env, limiter)
                    ds_ans = solver_answer(SOLVER_B, entry, spec, fig_urls, env, limiter)
                match = solve_match(str(glm_ans or ""), str(ds_ans or ""), key_row["type"], key_row["value"])
            except ValueError as exc:
                holds.append({
                    "q_no": q_no,
                    "reason": "empty_model" if "empty" in str(exc) else "solver_parse",
                    "detail": str(exc),
                    "decision": None,
                })
            except Exception as exc:
                holds.append({
                    "q_no": q_no,
                    "reason": "solver_parse",
                    "detail": f"{type(exc).__name__}: {exc}",
                    "decision": None,
                })
            if glm_ans is not None and ds_ans is not None and not match:
                holds.append({
                    "q_no": q_no,
                    "reason": "solver_mismatch",
                    "pdf_key": key_row["value"],
                    "glm": glm_ans,
                    "deepseek": ds_ans,
                    "stem_preview": (entry.get("body") or "")[:160],
                    "decision": None,
                })
        solvers[str(q_no)] = {
            "glm": glm_ans,
            "deepseek": ds_ans,
            "key": None if key_row is None else key_row["value"],
            "match": match,
        }
        dump(solvers_path, solvers)

        confidence = 1.0 if vision_ok else 0.5
        gates = {
            "skeleton": True,
            "shape_ok": shape_ok,
            "coverage_ok": coverage_ok,
            "vision_ok": vision_ok,
            "figures_ok": figures_ok,
            "audit_ok": audit_ok and dump_ok,
            "katex_ok": katex_ok,
            "solve_match": match,
            "confidence": confidence,
        }
        status = final_publish_status(gates, entry.get("body") or "")
        if status != "auto_ok":
            status = "unreviewed"
        answer = None if key_row is None else str(key_row["value"])
        upsert_question(
            sb, q_ids[q_no], entry, status,
            1.0 if status == "auto_ok" else 0.5,
            spec, answer=answer if status == "auto_ok" else None,
        )

    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})
    dump(out_dir / "solvers.json", solvers)
    dump(out_dir / "katex.json", katex_log)
    write_hold_json(out_dir, CHAPTER_NO, holds)
    report = build_report(CHAPTER_NO, holds)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)

    auto_ok = sum(1 for row in solvers.values() if row.get("match"))
    # recount from intended status rules
    pub = 0
    held_n = 0
    katex_holds = sorted({h["q_no"] for h in holds if h.get("reason") == "katex_render" and h.get("q_no")})
    fig_holds = [h.get("figure_key") for h in holds if h.get("reason") == "figure_get"]
    rows = sb.table("pyq_questions").select("q_no,review_status").eq("chapter_id", ch_id).execute().data
    by_status = {}
    for r in rows:
        by_status[r["review_status"]] = by_status.get(r["review_status"], 0) + 1
        if r["review_status"] in ("auto_ok", "human_ok"):
            pub += 1
        else:
            held_n += 1
    print("DB status", by_status, flush=True)
    print(f"slug=permutation-combination publishable={pub} held={held_n}", flush=True)
    print(f"katex_holds={katex_holds} figure_holds={fig_holds}", flush=True)
    print(f"solver_match_rows={auto_ok} vision_ok={len(vision_ok_q)}", flush=True)
    return 2 if holds else 0


if __name__ == "__main__":
    sys.exit(main())
