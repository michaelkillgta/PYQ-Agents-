"""Retry the four remaining 2025 paper-OCR holds and publish them."""
from __future__ import annotations

import json
from pathlib import Path

import pyq_common as p
from ingest_math_2025_paper_solutions import (
    BOOKS,
    dump,
    ocr_one,
    packet_for,
    publish_packets,
    run_ocr,
)

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
RETRY = [
    ("2025-jan", "di", 10, False),
    ("2025-apr", "di", 4, False),
    ("2025-jan", "de", 1, True),
    ("2025-apr", "de", 1, True),
]


def load_job(booklet: str, section: str, pdf_q: int) -> dict:
    book = next(b for b in BOOKS if b["id"] == booklet)
    jobs = json.loads((book["out"] / "jobs.json").read_text(encoding="utf-8"))
    rec = next(j for j in jobs if j["section"] == section and int(j["pdf_q"]) == pdf_q)
    rec["crop"] = Path(rec["crop"])
    rec["key_png"] = Path(rec["key_png"])
    rec["fig_png"] = Path(rec["fig_png"])
    rec["cache"] = Path(rec["cache"])
    rec["pdf_q"] = int(rec["pdf_q"])
    return rec


def main() -> int:
    env = p.load_env()
    sb = p.supabase_client()
    need_ocr = []
    rebuild = []
    for booklet, section, pdf_q, force in RETRY:
        job = load_job(booklet, section, pdf_q)
        if force and job["cache"].exists():
            job["cache"].unlink()
            print(f"deleted cache {job['cache'].name}", flush=True)
        if force or not job["cache"].exists():
            need_ocr.append(job)
        else:
            rebuild.append(job)
    packets = []
    if need_ocr:
        results = run_ocr(need_ocr, env)
        packets.extend(packet_for(item) for item in results)
    limiter = p.RateLimiter(18)
    for job in rebuild:
        data = ocr_one(job, env, limiter)
        packets.append(packet_for({"ok": True, "job": job, "data": data}))
    for pkt in packets:
        print(pkt["booklet"], pkt["section"], pkt["pdf_q"], pkt.get("hold"), flush=True)
        if pkt.get("solution_md"):
            print(pkt["solution_md"][:240], flush=True)
    dump(ROOT / "retry_packets.json", packets)
    summary = publish_packets(sb, packets)
    print(f"written {summary['written']}/{len(packets)} holds {len(summary['holds'])}", flush=True)
    return 0 if not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
