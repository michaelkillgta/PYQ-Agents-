#!/usr/bin/env python3
"""Revert hallucinated vision inserts; keep only the printed Q7 factorization."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from ingest_math_2025_paper_solutions import BOOKS
from ingest_math_2026_jan_di_solutions import dump
from layout_math_2025_paper_steps import layout_one
from layout_math_2026_jan_di_steps import paper_lines

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
Q7_ID = "b10a9ed1-33ca-4723-b7c0-74c3c820d8d0"
NEEDLE = "$f'(x) = x(x^2 - 9x + 20), x \\in (1, 5)$\n"
INSERT = NEEDLE + "$= (x-4)x(x-5)$\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    patches = json.loads((ROOT / "missing_line_patches.json").read_text(encoding="utf-8"))
    ids = {p_["id"] for p_ in patches}
    packets = json.loads((ROOT / "packets.json").read_text(encoding="utf-8"))
    by_id = {p_["row_id"]: p_ for p_ in packets if p_.get("row_id")}
    for pkt in packets:
        if pkt.get("row_id") == Q7_ID and "$= (x-4)x(x-5)$" not in (pkt.get("solution_md") or ""):
            pkt["solution_md"] = (pkt["solution_md"] or "").replace(NEEDLE, INSERT, 1)
    (ROOT / "packets.json").write_text(
        json.dumps(packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    jan = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-solutions\packets.json")
    jan_packets = json.loads(jan.read_text(encoding="utf-8"))
    for pkt in jan_packets:
        if pkt.get("row_id") == Q7_ID and "$= (x-4)x(x-5)$" not in (pkt.get("solution_md") or ""):
            pkt["solution_md"] = (pkt["solution_md"] or "").replace(NEEDLE, INSERT, 1)
    jan.write_text(json.dumps(jan_packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    env = p.load_env()
    sb = p.supabase_client()
    jobs = []
    for rid in sorted(ids):
        pkt = by_id[rid]
        if rid == Q7_ID:
            md = next(p_["solution_md"] for p_ in packets if p_["row_id"] == Q7_ID)
        else:
            md = pkt["solution_md"]
        book = next(b for b in BOOKS if b["id"] == pkt["booklet"])
        cache = book["out"] / "steps" / f"{pkt['section']}_q{pkt['pdf_q']:02d}.json"
        if cache.exists():
            cache.unlink()
        miss = book["out"] / "miss_audit" / f"{pkt['section']}_q{pkt['pdf_q']:02d}.json"
        if miss.exists():
            miss.unlink()
        jobs.append({
            "booklet": pkt["booklet"],
            "section": pkt["section"],
            "pdf_q": pkt["pdf_q"],
            "id": rid,
            "pdf_key": pkt.get("pdf_key") or "",
            "label": f"{pkt['booklet']} {pkt['section']} Q{pkt['pdf_q']}",
            "lines": paper_lines(md),
            "cache": cache,
        })
    limiter = p.RateLimiter(18)
    print(f"re-layout {len(jobs)} (Q7 keep factorization; others restore packet)", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futs = [pool.submit(layout_one, job, env, limiter) for job in jobs]
        for fut in as_completed(futs):
            results.append(fut.result())
    for item in results:
        sb.table("pyq_questions").update({"solution_md": item["solution_md"]}).eq(
            "id", item["id"]
        ).execute()
        print(f"  [live] {item['label']}", flush=True)
        if item["id"] == Q7_ID:
            assert "$= (x-4)x(x-5)$" in item["solution_md"]
            assert "$= (x-4)(x-5)$" not in item["solution_md"].replace("$= (x-4)x(x-5)$", "")
    dump(ROOT / "q7_factor_publish.json", {
        "written": [r["label"] for r in results],
        "q7_has_factor": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
