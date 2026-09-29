#!/usr/bin/env python3
"""Push a small Application of Derivatives repair dict to DB (human_ok)."""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p

CHAPTER = 17


def push_repairs(repairs: dict) -> None:
    p.configure_book("math")
    sb = p.supabase_client()
    cid = p.resolve_chapter_id(sb, CHAPTER, "Mathematics")
    rows = sb.table("pyq_questions").select("id,q_no").eq("chapter_id", cid).execute().data
    q_by_no = {int(r["q_no"]): r["id"] for r in rows}
    for q_no, data in sorted(repairs.items()):
        qid = q_by_no.get(int(q_no))
        if not qid:
            print(f"MISSING Q{q_no}")
            continue
        fmt = data["format"]
        patch = {
            "format": fmt,
            "body": data["body"].strip(),
            "review_status": "human_ok",
            "extraction_confidence": 1.0,
            "correct_option": data.get("correct_option"),
            "numerical_answer": data.get("numerical_answer"),
        }
        sb.table("pyq_questions").update(patch).eq("id", qid).execute()
        sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
        if fmt == "mcq" and data.get("options"):
            sb.table("pyq_question_options").insert(
                [
                    {"question_id": qid, "option_index": i, "body": opt.strip()}
                    for i, opt in enumerate(data["options"], start=1)
                ]
            ).execute()
        key = data.get("numerical_answer") if fmt == "numerical" else data.get("correct_option")
        print(f"Q{int(q_no):3d} [{fmt:9s}] -> {key}", flush=True)
    print(f"batch done ({len(repairs)} questions)")
