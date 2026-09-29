#!/usr/bin/env python3
"""Emergency: publish math PDF ch.25-33 from parsed.json or OCR cache.

No Document AI. No Gemini. auto_ok rows are kept. Shape+KaTeX+figures+PDF key
become human_ok; the rest stay unreviewed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyq_common as p
from run_chapter_agents import chapter_dir, dump, parse_pages, spec_map
from agents.figures_check import (
    chapter_figure_keys,
    http_get_status,
    missing_figure_gets,
    upload_chapter_figures,
)
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.publish import shape_ok_for, upsert_question

SLUG = {
    25: "ellipse",
    26: "hyperbola",
    27: "trigonometric-ratios-and-identities",
    28: "trigonometric-equations",
    29: "inverse-trigonometric-functions",
    30: "trigonometric-ratios-and-identities",
    31: "trigonometric-ratios-and-identities",
    32: "vector-algebra",
    33: "three-dimensional-geometry",
}


def _is_missed(entry: dict | None) -> bool:
    if not entry:
        return True
    body = (entry.get("body") or "").strip()
    return (not body) or body.startswith("(OCR missed")


def parse_from_ocr(chapter_no: int, skeleton_all: list, specs: dict) -> tuple[dict, list, dict]:
    pages = sorted({r["page"] for r in specs.values()})
    digitise: dict = {}
    missing_ocr: list[int] = []
    for page_no in pages:
        cache = p.OUT / "ocr" / f"page_{page_no:03d}.json"
        if not cache.exists():
            missing_ocr.append(page_no)
            continue
        digitise[page_no] = json.loads(cache.read_text(encoding="utf-8"))
    parsed, failures, _by_page = parse_pages(skeleton_all, chapter_no, digitise)
    return parsed, missing_ocr, failures


def load_or_parse(chapter_no: int, skeleton_all: list, specs: dict) -> tuple[dict, list]:
    """Reuse parsed.json stems; fill OCR-missed rows from cache. Never Document AI."""
    out_dir = chapter_dir(chapter_no)
    out_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = out_dir / "parsed.json"
    existing: dict[int, dict] = {}
    if parsed_path.exists():
        raw = json.loads(parsed_path.read_text(encoding="utf-8"))
        existing = {int(k): v for k, v in raw.items()}
    ocr_parsed, missing_ocr, failures = parse_from_ocr(chapter_no, skeleton_all, specs)
    merged = dict(existing)
    filled = 0
    for q_no, entry in ocr_parsed.items():
        if _is_missed(merged.get(q_no)) and not _is_missed(entry):
            merged[q_no] = entry
            filled += 1
        elif q_no not in merged:
            merged[q_no] = entry
            filled += 1
    dump(out_dir / "parsed.json", {str(k): v for k, v in merged.items()})
    dump(out_dir / "parse_failures.json", failures)
    still_miss = sum(1 for q in specs if _is_missed(merged.get(q)))
    print(
        f"  merge existing={len(existing)} ocr={len(ocr_parsed)} "
        f"filled={filled} still_miss={still_miss} missing_ocr={missing_ocr}",
        flush=True,
    )
    return merged, missing_ocr


def publish_chapter(chapter_no: int, skeleton_all: list, sb) -> dict:
    specs = spec_map(skeleton_all, chapter_no)
    print(f"chapter {chapter_no} {SLUG[chapter_no]} q={len(specs)}", flush=True)
    parsed, missing_ocr = load_or_parse(chapter_no, skeleton_all, specs)

    wanted_keys = chapter_figure_keys(skeleton_all, chapter_no)
    missing_figs: list[str] = []
    ok_fig_keys: set[str] = set()
    if wanted_keys:
        fig_urls = upload_chapter_figures(chapter_no, sb)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
        if missing_figs:
            fig_urls = upload_chapter_figures(chapter_no, sb)
            key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
            missing_figs = missing_figure_gets(key_to_url, http_get_status)
        ok_fig_keys = {k for k in wanted_keys if k not in missing_figs}
        print(f"  figures wanted={wanted_keys} missing={missing_figs}", flush=True)

    ch_id = p.resolve_chapter_id(sb, chapter_no, "Mathematics")
    q_rows = (
        sb.table("pyq_questions")
        .select("id,q_no,review_status")
        .eq("chapter_id", ch_id)
        .execute()
        .data
    )
    q_ids = {int(r["q_no"]): r["id"] for r in q_rows}
    existing = {int(r["q_no"]): r["review_status"] for r in q_rows}

    holds: list[dict] = []
    for key in missing_figs:
        holds.append({"q_no": None, "reason": "figure_get", "figure_key": key, "decision": None})
    for page_no in missing_ocr:
        holds.append({"q_no": None, "reason": "missing_ocr", "page": page_no, "decision": None})

    kept_auto = 0
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no) or {}
        if existing.get(q_no) == "auto_ok":
            kept_auto += 1
            continue
        body = entry.get("body") or ""
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", body)
        figures_ok = all(k in ok_fig_keys for k in body_figs)
        if not figures_ok:
            holds.append({"q_no": q_no, "reason": "figure_get", "decision": None})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        if is_solver_dump(body):
            holds.append({"q_no": q_no, "reason": "solver_prose", "decision": None})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        fields = [body, *(entry.get("options") or [])]
        if not all(katex_render_ok(t) for t in fields):
            holds.append({"q_no": q_no, "reason": "katex_render", "decision": None})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        if not shape_ok_for(spec, entry):
            holds.append({"q_no": q_no, "reason": "shape", "decision": None})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        upsert_question(
            sb,
            q_ids[q_no],
            entry,
            "human_ok",
            1.0,
            spec,
            answer=str(spec.get("answer_value") or ""),
        )

    dump(chapter_dir(chapter_no) / "emergency_hold.json", {"chapter_no": chapter_no, "holds": holds})
    rows = (
        sb.table("pyq_questions")
        .select("q_no,review_status")
        .eq("chapter_id", ch_id)
        .execute()
        .data
    )
    auto = sum(1 for r in rows if r["review_status"] == "auto_ok")
    human = sum(1 for r in rows if r["review_status"] == "human_ok")
    pub = auto + human
    held = len(rows) - pub
    katex_q = sorted(h["q_no"] for h in holds if h.get("reason") == "katex_render" and h.get("q_no"))
    fig_q = sorted(
        str(h.get("q_no") or h.get("figure_key"))
        for h in holds
        if h.get("reason") == "figure_get"
    )
    print(
        f"  DONE pub={pub} (auto={auto} human={human}) held={held} "
        f"katex={len(katex_q)} fig={len(fig_q)} kept_auto={kept_auto}",
        flush=True,
    )
    return {
        "chapter": chapter_no,
        "slug": SLUG[chapter_no],
        "n": len(rows),
        "publishable": pub,
        "auto_ok": auto,
        "human_ok": human,
        "held": held,
        "katex_holds": katex_q,
        "figure_holds": fig_q,
    }


def main() -> int:
    p.configure_book("math")
    skeleton_all = p.load_skeleton()
    sb = p.supabase_client()
    rows = []
    for n in range(25, 34):
        rows.append(publish_chapter(n, skeleton_all, sb))
    print("\nCHAPTER\tSLUG\tPUBLISHABLE\tHELD\tAUTO\tHUMAN\tKATEX\tFIGURE")
    for r in rows:
        kx = ",".join(str(q) for q in r["katex_holds"]) or "-"
        fg = ",".join(r["figure_holds"]) or "-"
        print(
            f"{r['chapter']}\t{r['slug']}\t{r['publishable']}/{r['n']}\t"
            f"{r['held']}\t{r['auto_ok']}\t{r['human_ok']}\t{kx}\t{fg}"
        )
    dump(p.OUT / "agents" / "emergency_25_33_summary.json", rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
