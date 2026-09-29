#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import pyq_common as p

p.configure_book("math")
REPAIRS = json.loads(Path("out-math/agents/chapter_23/fill_gate_repairs.json").read_text(encoding="utf-8"))
sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 23, "Mathematics")
rows = sb.table("pyq_questions").select("id,q_no").eq("chapter_id", cid).execute().data
q_by_no = {r["q_no"]: r["id"] for r in rows}

for q_s, data in sorted(REPAIRS.items(), key=lambda kv: int(kv[0])):
    q_no = int(q_s)
    qid = q_by_no[q_no]
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
    print(f"fill-gate repaired Q{q_no}")
print("done")
