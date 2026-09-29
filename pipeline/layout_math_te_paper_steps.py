#!/usr/bin/env python3
"""Cut Trigonometric Equations paper OCR into labeled steps. gemma4 text only."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import VISION_MODEL
from ingest_math_2026_jan_di_solutions import PAPER_MARKER, dump
from ingest_math_te_paper_solutions import BOOKS, fetch_rows
from layout_math_2025_paper_steps import layout_one
from layout_math_2026_jan_di_steps import paper_lines

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-te-solutions")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT.mkdir(parents=True, exist_ok=True)
    env = p.load_env()
    sb = p.supabase_client()
    rows = fetch_rows(sb)
    jobs = []
    books = {b["id"]: b for b in BOOKS}
    for row in rows.values():
        bbox = row.get("source_bbox") or {}
        booklet = str(bbox.get("booklet") or "")
        pdf_q = int(bbox.get("pdf_q"))
        md = row.get("solution_md") or ""
        if PAPER_MARKER not in md:
            continue
        lines = paper_lines(md)
        if not lines:
            print(f"empty paper {booklet} Q{pdf_q}", flush=True)
            continue
        book = books[booklet]
        steps_dir = book["out"] / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)
        key = (
            str(row.get("numerical_answer") or "").strip()
            if str(row.get("format") or "") == "numerical"
            else str(row.get("correct_option") or "").strip()
        )
        jobs.append({
            "booklet": booklet,
            "section": "te",
            "pdf_q": pdf_q,
            "id": row["id"],
            "pdf_key": key,
            "label": f"{booklet} te Q{pdf_q}",
            "lines": lines,
            "cache": steps_dir / f"te_q{pdf_q:02d}.json",
        })
    print(f"{len(jobs)} TE paper packets to partition", flush=True)
    limiter = p.RateLimiter(18)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(layout_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                item = fut.result()
                results.append(item)
                tag = "cached" if item.get("cached") else "ok"
                print(f"  [{tag}] {job['label']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "error": str(exc), **job})
                print(f"  [fail] {job['label']} {exc}", flush=True)
    written = 0
    holds = []
    for item in sorted(results, key=lambda r: (r["booklet"], int(r["pdf_q"]))):
        if not item.get("ok") or not item.get("solution_md"):
            holds.append({"label": item.get("label"), "reason": item.get("error") or "layout"})
            continue
        sb.table("pyq_questions").update({"solution_md": item["solution_md"]}).eq(
            "id", item["id"]
        ).execute()
        written += 1
        print(f"  [steps] {item['label']}", flush=True)
    dump(ROOT / "layout_publish.json", {"written": written, "holds": holds})
    print(f"written {written}/{len(jobs)} holds {len(holds)}", flush=True)
    return 0 if written == len(jobs) and not holds else 2


if __name__ == "__main__":
    raise SystemExit(main())
