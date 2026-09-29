#!/usr/bin/env python3
"""Emergency publish math ch.11–16 from parsed.json or cached OCR. No Document AI unless OCR missing."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyq_common as p
from agents.figures_check import (
    chapter_figure_keys,
    http_get_status,
    missing_figure_gets,
    upload_chapter_figures,
)
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.publish import promote_shape_valid, shape_ok_for, upsert_question
from agents.report import build_report
from parse_ocr_page import parse_digitise_to_questions
from bakeoff import page_slice

SLUGS = {
    11: "probability",
    12: "sets-and-relations",
    13: "functions",
    14: "limits",
    15: "continuity-and-differentiability",
    16: "differentiation",
}
FIG_RE = re.compile(r"\[\[fig:([^\]]+)\]\]")


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def load_ocr_cached(pages: list[int]) -> tuple[dict, list[int]]:
    digitise, missing = {}, []
    for page_no in pages:
        cache = p.OUT / "ocr" / f"page_{page_no:03d}.json"
        if cache.exists():
            digitise[page_no] = json.loads(cache.read_text(encoding="utf-8"))
        else:
            missing.append(page_no)
            digitise[page_no] = "missing ocr"
    return digitise, missing


def parse_from_ocr(skeleton: list, chapter_no: int, digitise: dict) -> dict:
    parsed = {}
    pages = sorted({r["page"] for r in skeleton if r["chapter_no"] == chapter_no})
    for page_no in pages:
        payload = digitise.get(page_no)
        if isinstance(payload, str) or payload is None:
            print(f"  skip parse page {page_no}: {payload}", flush=True)
            continue
        slice_ = page_slice(skeleton, page_no)
        try:
            questions = parse_digitise_to_questions(payload, slice_)
            p.validate_page_response({"questions": questions}, {s["q_no"] for s in slice_},
                                     {k for s in slice_ for k in s["figure_keys"]})
        except Exception as exc:
            print(f"  parse fail page {page_no}: {type(exc).__name__}: {exc}", flush=True)
            continue
        for q in questions:
            parsed[str(int(q["q_no"]))] = {
                "body": q["body"],
                "options": q.get("options"),
                "page": page_no,
            }
    return parsed


def row_katex_ok(entry: dict) -> bool:
    fields = [entry.get("body") or ""]
    fields.extend(entry.get("options") or [])
    if is_solver_dump(fields[0]):
        return False
    return all(katex_render_ok(t) for t in fields)


def db_counts(sb, ch_id: str) -> dict[str, int]:
    rows = (sb.table("pyq_questions").select("q_no,review_status,body")
            .eq("chapter_id", ch_id).execute().data)
    out = {"n": len(rows), "auto_ok": 0, "human_ok": 0, "unreviewed": 0, "other": 0}
    for r in rows:
        st = r.get("review_status") or "other"
        if st in out:
            out[st] += 1
        else:
            out["other"] += 1
    out["publishable"] = out["auto_ok"] + out["human_ok"]
    out["held"] = out["n"] - out["publishable"]
    return out


def main() -> int:
    spec = p.configure_book("math")
    skeleton_all = p.load_skeleton()
    sb = p.supabase_client()
    table = []
    for chapter_no in range(11, 17):
        print(f"=== chapter {chapter_no} {SLUGS[chapter_no]} ===", flush=True)
        rows = [r for r in skeleton_all if r["chapter_no"] == chapter_no]
        if not rows:
            table.append({"n": chapter_no, "slug": SLUGS[chapter_no], "error": "no skeleton"})
            continue
        out_dir = p.OUT / "agents" / f"chapter_{chapter_no}"
        out_dir.mkdir(parents=True, exist_ok=True)
        parsed_path = out_dir / "parsed.json"
        pages = sorted({r["page"] for r in rows})
        if parsed_path.exists():
            parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
            print(f"  reuse parsed.json n={len(parsed)}", flush=True)
        else:
            digitise, ocr_missing = load_ocr_cached(pages)
            if ocr_missing:
                env = p.load_env()
                print(f"  OCR missing pages {ocr_missing}; Document AI those only", flush=True)
                for page_no in ocr_missing:
                    try:
                        digitise[page_no] = p.digitise_page(page_no, env["SARVAM_API_KEY"])
                    except Exception as exc:
                        digitise[page_no] = f"{type(exc).__name__}: {exc}"
            parsed = parse_from_ocr(skeleton_all, chapter_no, digitise)
            dump(parsed_path, parsed)
            print(f"  wrote parsed.json n={len(parsed)}/{len(rows)}", flush=True)

        fig_urls = upload_chapter_figures(chapter_no, sb)
        wanted = chapter_figure_keys(skeleton_all, chapter_no)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
        if missing_figs:
            fig_urls = upload_chapter_figures(chapter_no, sb)
            key_to_url = {k: fig_urls.get(k, "") for k in wanted}
            missing_figs = missing_figure_gets(key_to_url, http_get_status)
        print(f"  figures wanted={len(wanted)} missing_get={missing_figs}", flush=True)

        try:
            ch_id = p.resolve_chapter_id(sb, chapter_no, spec["subject_name"])
        except Exception as exc:
            table.append({
                "n": chapter_no, "slug": SLUGS[chapter_no],
                "error": f"resolve_chapter_id: {exc}",
                "parsed": len(parsed), "fig_hold": len(missing_figs),
            })
            continue

        specs = {int(r["q_no"]): r for r in rows}
        q_rows = (sb.table("pyq_questions").select("id,q_no,review_status")
                  .eq("chapter_id", ch_id).execute().data)
        q_ids = {int(r["q_no"]): r["id"] for r in q_rows}
        existing = {int(r["q_no"]): r["review_status"] for r in q_rows}

        # Hold figure-token rows whose GET failed, then shape/KaTeX promote the rest.
        fig_holds = []
        katex_holds = []
        skip_promote = set()
        for q_no, spec_row in specs.items():
            entry = parsed.get(str(q_no)) or parsed.get(q_no) or {}
            body_figs = FIG_RE.findall((entry.get("body") if isinstance(entry, dict) else "") or "")
            if any(k in missing_figs for k in body_figs) or any(
                k in missing_figs for k in (spec_row.get("figure_keys") or [])
            ):
                if q_no in q_ids and existing.get(q_no) != "auto_ok":
                    upsert_question(sb, q_ids[q_no], entry if isinstance(entry, dict) else {},
                                    "unreviewed", 0.5, spec_row)
                fig_holds.append(q_no)
                skip_promote.add(q_no)
                continue
            fields = []
            if isinstance(entry, dict):
                fields = [entry.get("body") or ""]
                fields.extend(entry.get("options") or [])
            if isinstance(entry, dict) and (
                is_solver_dump(entry.get("body") or "") or not all(katex_render_ok(t) for t in fields)
            ):
                katex_holds.append(q_no)

        existing_for_promote = dict(existing)
        for q_no in skip_promote:
            existing_for_promote[q_no] = "auto_ok"  # skip promote overwrite
        promoted, held = promote_shape_valid(sb, q_ids, specs, parsed, existing_for_promote)
        # Re-apply figure holds in case promote overwrote (we marked skip as auto_ok so it shouldn't)

        counts = db_counts(sb, ch_id)
        holds_payload = (
            [{"q_no": q, "reason": "figure_get"} for q in fig_holds]
            + [{"q_no": q, "reason": "katex_render"} for q in katex_holds]
        )
        dump(out_dir / "hold.json", {"chapter_no": chapter_no, "holds": holds_payload})
        (out_dir / "REPORT.md").write_text(
            build_report(chapter_no, holds_payload), encoding="utf-8"
        )
        row = {
            "n": chapter_no,
            "slug": SLUGS[chapter_no],
            "parsed": len(parsed),
            "skeleton": len(rows),
            "publishable": counts["publishable"],
            "held": counts["held"],
            "auto_ok": counts["auto_ok"],
            "human_ok": counts["human_ok"],
            "unreviewed": counts["unreviewed"],
            "fig_hold": len(fig_holds),
            "katex_hold": len(katex_holds),
            "missing_fig_keys": missing_figs,
            "promoted_this_pass": promoted,
            "held_this_pass": held,
        }
        table.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)

    print("TABLE", flush=True)
    print(json.dumps(table, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
