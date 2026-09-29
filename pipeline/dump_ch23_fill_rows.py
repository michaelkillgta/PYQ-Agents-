#!/usr/bin/env python3
"""Dump Circle rows for the TypeScript isPyqPaperFilled gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import pyq_common as p

p.configure_book("math")
sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 23, "Mathematics")
rows = (
    sb.table("pyq_questions")
    .select("q_no,review_status,format,numerical_answer,body,pyq_question_options(option_index,body)")
    .eq("chapter_id", cid)
    .order("q_no")
    .execute()
    .data
)
out = []
for r in rows:
    opts = sorted(r.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    out.append(
        {
            "q_no": r["q_no"],
            "review_status": r["review_status"],
            "body": r["body"],
            "format": r["format"],
            "numerical_answer": r.get("numerical_answer"),
            "question_options": [{"option_index": o["option_index"], "body": o["body"]} for o in opts],
        }
    )
path = Path(r"c:\Users\tempo\Downloads\EduBlast\Web\scripts\_circle_fill_rows.json")
path.write_text(json.dumps(out), encoding="utf-8")
print(f"wrote {len(out)} rows to {path}")
