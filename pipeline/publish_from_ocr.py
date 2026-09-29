#!/usr/bin/env python3
"""Publish math chapters from parsed.json or OCR cache. Document AI only if a page JSON is missing."""
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
from agents.publish import shape_ok_for, upsert_question
from agents.report import build_report
from audit_paper_text import flags_for
from run_chapter_agents import chapter_dir, dump, parse_pages, row_audit_ok, spec_map

SLUGS = {
    17: "application-of-derivatives",
    18: "indefinite-integration",
    19: "definite-integration",
    20: "area-under-curves",
    21: "differential-equations",
    22: "straight-lines",
    23: "circle",
    24: "parabola",
}


def load_digitise(pages: list[int]) -> dict:
    digitise = {}
    env = None
    for page_no in pages:
        cache = p.OUT / "ocr" / f"page_{page_no:03d}.json"
        if cache.exists():
            digitise[page_no] = json.loads(cache.read_text(encoding="utf-8"))
            continue
        if env is None:
            env = p.load_env()
        digitise[page_no] = p.digitise_page(page_no, env["SARVAM_API_KEY"])
    return digitise


def parsed_as_int(raw: dict) -> dict[int, dict]:
    out = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            out[int(k)] = v
    return out


def publish_chapter(chapter_no: int) -> dict:
    book_spec = p.configure_book("math")
    skeleton_all = p.load_skeleton()
    specs = spec_map(skeleton_all, chapter_no)
    if not specs:
        raise SystemExit(f"no skeleton rows for chapter {chapter_no}")
    out_dir = chapter_dir(chapter_no)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted({r["page"] for r in specs.values()})
    parsed_path = out_dir / "parsed.json"

    if parsed_path.exists():
        parsed = parsed_as_int(json.loads(parsed_path.read_text(encoding="utf-8")))
        parse_failures = {}
        source = "parsed.json"
    else:
        digitise = load_digitise(pages)
        parsed, parse_failures, _by_page = parse_pages(skeleton_all, chapter_no, digitise)
        dump(out_dir / "parse_failures.json", parse_failures)
        dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})
        source = "ocr"

    sb = p.supabase_client()
    fig_urls = upload_chapter_figures(chapter_no, sb)
    wanted_keys = chapter_figure_keys(skeleton_all, chapter_no)
    key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
    missing_figs = missing_figure_gets(key_to_url, http_get_status)
    if missing_figs:
        fig_urls = upload_chapter_figures(chapter_no, sb)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
    ok_fig_keys = {k for k in wanted_keys if k not in missing_figs}

    ch_id = p.resolve_chapter_id(sb, chapter_no, book_spec["subject_name"])
    q_rows = sb.table("pyq_questions").select("id,q_no,review_status").eq(
        "chapter_id", ch_id).execute().data
    q_ids = {int(r["q_no"]): r["id"] for r in q_rows}
    existing = {int(r["q_no"]): r["review_status"] for r in q_rows}

    holds = []
    for key in missing_figs:
        holds.append({"q_no": None, "reason": "figure_get", "figure_key": key, "decision": None})

    katex_holds = 0
    figure_holds = len(missing_figs)
    kept_auto = 0
    published = 0
    held_q = set()

    for q_no, spec in sorted(specs.items()):
        if existing.get(q_no) == "auto_ok":
            kept_auto += 1
            published += 1
            continue
        entry = parsed.get(q_no) or {}
        reasons = []
        if q_no not in parsed:
            reasons.append("coverage_miss")
        body = entry.get("body") or ""
        if is_solver_dump(body):
            reasons.append("solver_prose")
        fields = [body]
        fields.extend(entry.get("options") or [])
        if not all(katex_render_ok(t) for t in fields):
            reasons.append("katex_render")
            katex_holds += 1
        if not shape_ok_for(spec, entry):
            reasons.append("shape")
        if not row_audit_ok(entry):
            reasons.append("truncated")
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", body)
        if not all(k in ok_fig_keys for k in body_figs):
            reasons.append("figure_get")
            figure_holds += 1
        key_val = spec.get("answer_value")
        if key_val is None or str(key_val).strip() == "":
            reasons.append("pdf_key")

        if reasons:
            held_q.add(q_no)
            for reason in reasons:
                holds.append({"q_no": q_no, "reason": reason, "decision": None})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue

        upsert_question(
            sb, q_ids[q_no], entry, "human_ok", 1.0, spec,
            answer=str(key_val),
        )
        published += 1

    dump(out_dir / "hold.json", {"chapter_no": chapter_no, "holds": holds})
    report = build_report(chapter_no, holds)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")

    fresh = sb.table("pyq_questions").select("q_no,review_status").eq(
        "chapter_id", ch_id).execute().data
    auto_ok = sum(1 for r in fresh if r["review_status"] == "auto_ok")
    human_ok = sum(1 for r in fresh if r["review_status"] == "human_ok")
    publishable = auto_ok + human_ok
    held = len(fresh) - publishable
    return {
        "chapter": chapter_no,
        "slug": SLUGS[chapter_no],
        "source": source,
        "skeleton": len(specs),
        "parsed": len(parsed),
        "publishable": publishable,
        "held": held,
        "auto_ok": auto_ok,
        "human_ok": human_ok,
        "figure_holds": figure_holds,
        "katex_holds": katex_holds,
        "parse_failures": len(parse_failures),
        "kept_auto_ok": kept_auto,
    }


def main(argv: list[str] | None = None) -> int:
    p.configure_book("math")
    p.load_env()
    start, end = 17, 24
    args = argv if argv is not None else sys.argv[1:]
    if len(args) == 2:
        start, end = int(args[0]), int(args[1])
    rows = []
    for n in range(start, end + 1):
        print(f"publishing chapter {n} {SLUGS[n]}", flush=True)
        row = publish_chapter(n)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    dump(p.OUT / "agents" / "emergency_17_24.json", rows)
    print("CHAPTER\tSLUG\tPUBLISHABLE\tHELD\tFIGURE_HOLDS\tKATEX_HOLDS", flush=True)
    for r in rows:
        print(
            f"{r['chapter']}\t{r['slug']}\t{r['publishable']}\t{r['held']}\t"
            f"{r['figure_holds']}\t{r['katex_holds']}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
