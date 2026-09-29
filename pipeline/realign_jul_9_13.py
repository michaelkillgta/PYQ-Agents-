#!/usr/bin/env python3
"""Put 2022 July Q9-Q13 on the printed headers."""
from __future__ import annotations

import json
import sys

import pyq_common as p
from finish_di_remaining import fetch_rows, pick_question, publish_row
from ingest_di_yearbooks import CHAPTER_NO, OUT, SUBJECT, BOOKLETS
from retry_di_tops import crop_page_top, observe, spec_of


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = json.loads((OUT / "all_skeleton.json").read_text(encoding="utf-8"))
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db = fetch_rows(sb, chapter_id)

    pdf = next(b["pdf"] for b in BOOKLETS if b["id"] == "2022-jul")
    sk = {int(r["q_no"]): r for r in skeleton if r["booklet"] == "2022-jul"}

    spec9 = spec_of("2022-jul", 9, "B", "mcq", sk[9])
    png = OUT / "2022-jul" / "crops" / "top_q09.png"
    crop_page_top(pdf, 4, png)
    data = observe(png, spec9, env, limiter)
    raw = pick_question(data, 9) or data
    ok, reason = publish_row(sb, db[("2022-jul", 9)], spec9, {
        "body": raw.get("body") or "", "options": raw.get("options"), "page": 4,
    }, env, limiter)
    print("Q9", reason, flush=True)

    retry = json.loads((OUT / "2022-jul" / "gemma4" / "page_004.retry.json").read_text(encoding="utf-8"))
    q10 = next(q for q in retry["questions"] if int(q["q_no"]) == 11)
    ok, reason = publish_row(
        sb, db[("2022-jul", 10)], spec_of("2022-jul", 10, "D", "mcq", sk[10]),
        {"body": q10["body"], "options": q10["options"], "page": 4}, env, limiter,
    )
    print("Q10", reason, flush=True)

    p5 = json.loads((OUT / "2022-jul" / "gemma4" / "page_005.json").read_text(encoding="utf-8"))
    by = {int(q["q_no"]): q for q in p5["questions"]}
    jobs = [
        (11, "B", "mcq", {"body": by[12]["body"], "options": by[12]["options"]}),
        (12, "385", "numerical", {"body": by[13]["body"], "options": None}),
        (13, "12", "numerical", {"body": by[14]["body"], "options": None}),
    ]
    for pdf_q, key, kind, entry in jobs:
        ok, reason = publish_row(
            sb, db[("2022-jul", pdf_q)], spec_of("2022-jul", pdf_q, key, kind, sk[pdf_q]),
            entry, env, limiter,
        )
        print(f"Q{pdf_q}", reason, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
