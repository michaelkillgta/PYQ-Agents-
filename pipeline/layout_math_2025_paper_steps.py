#!/usr/bin/env python3
"""Cut 2025 paper OCR into labeled steps. gemma4 text only. No glm. No re-OCR.

    python layout_math_2025_paper_steps.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import VISION_MODEL
from ingest_math_2025_paper_solutions import BOOKS, fetch_rows, section_of
from ingest_math_2026_jan_di_solutions import PAPER_MARKER, dump
from layout_math_2026_jan_di_steps import (
    LAYOUT_SYSTEM,
    assemble_steps,
    heuristic_cuts,
    numbered_list,
    paper_lines,
    validate_cuts,
)
from run_chapter_agents import v2_json

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")


def ask_cuts(lines: list[str], label: str, key: str, env: dict, limiter: p.RateLimiter) -> list[dict]:
    user = (
        f"{label}. Official key {key}. "
        "Assign every line to a step.\n\n"
        + numbered_list(lines)
    )
    messages = [
        {"role": "system", "content": LAYOUT_SYSTEM},
        {"role": "user", "content": user},
    ]
    last_err = None
    for _ in range(3):
        try:
            data = v2_json(VISION_MODEL, messages, env, limiter)
            cuts = validate_cuts(len(lines), list(data.get("steps") or []))
            if cuts:
                return cuts
            last_err = ValueError("coverage")
        except Exception as exc:
            last_err = exc
    print(f"  {label} gemma cuts failed ({last_err}); heuristic", flush=True)
    return heuristic_cuts(lines)


def layout_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache: Path = job["cache"]
    lines: list[str] = job["lines"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        cuts = validate_cuts(len(lines), list(data.get("steps") or []))
        if cuts:
            md = assemble_steps(lines, cuts)
            return {**job, "ok": True, "solution_md": md, "cached": True}
    cuts = ask_cuts(lines, job["label"], job["pdf_key"], env, limiter)
    dump(cache, {"label": job["label"], "steps": cuts, "_model": VISION_MODEL})
    md = assemble_steps(lines, cuts)
    return {**job, "ok": True, "solution_md": md, "cached": False}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT.mkdir(parents=True, exist_ok=True)
    env = p.load_env()
    sb = p.supabase_client()
    rows = fetch_rows(sb)
    jobs = []
    for row in rows.values():
        bbox = row.get("source_bbox") or {}
        booklet = str(bbox.get("booklet") or "")
        pdf_q = int(bbox.get("pdf_q"))
        section = section_of(bbox)
        md = row.get("solution_md") or ""
        if "paper-ocr" not in md:
            continue
        lines = paper_lines(md)
        if not lines:
            print(f"empty paper {booklet} {section} Q{pdf_q}", flush=True)
            continue
        book = next(b for b in BOOKS if b["id"] == booklet)
        steps_dir = book["out"] / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)
        key = (
            str(row.get("numerical_answer") or "").strip()
            if str(row.get("format") or "") == "numerical"
            else str(row.get("correct_option") or "").strip()
        )
        jobs.append({
            "booklet": booklet,
            "section": section,
            "pdf_q": pdf_q,
            "id": row["id"],
            "pdf_key": key,
            "label": f"{booklet} {section} Q{pdf_q}",
            "lines": lines,
            "cache": steps_dir / f"{section}_q{pdf_q:02d}.json",
        })
    expect = 63
    print(f"{len(jobs)} paper packets to partition (expect {expect})", flush=True)
    if len(jobs) != expect:
        raise SystemExit(f"need {expect} paper packets, got {len(jobs)}")

    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} layout jobs in parallel | model={VISION_MODEL} | text only", flush=True)
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
    for item in sorted(results, key=lambda r: (r["booklet"], r["section"], int(r["pdf_q"]))):
        if not item.get("ok") or not item.get("solution_md"):
            holds.append({"label": item.get("label"), "reason": item.get("error") or "layout"})
            continue
        sb.table("pyq_questions").update({"solution_md": item["solution_md"]}).eq(
            "id", item["id"]
        ).execute()
        written += 1
        print(f"  [steps] {item['label']}", flush=True)
    dump(ROOT / "layout_publish.json", {"written": written, "holds": holds})
    print(f"written {written}/{expect} holds {len(holds)}", flush=True)
    return 0 if written == expect and not holds else 2


if __name__ == "__main__":
    raise SystemExit(main())
