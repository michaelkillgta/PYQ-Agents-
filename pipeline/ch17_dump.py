#!/usr/bin/env python3
"""Dump Application of Derivatives (ch17) rows for fill-gate + held audit."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import pyq_common as p

CHAPTER = 17
p.configure_book("math")
sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, CHAPTER, "Mathematics")

rows = (
    sb.table("pyq_questions")
    .select("id,q_no,format,body,review_status,correct_option,numerical_answer")
    .eq("chapter_id", cid)
    .order("q_no")
    .execute()
    .data
)
ids = [r["id"] for r in rows]
opts: dict[str, list] = {i: [] for i in ids}
for i in range(0, len(ids), 80):
    chunk = ids[i : i + 80]
    od = (
        sb.table("pyq_question_options")
        .select("question_id,option_index,body")
        .in_("question_id", chunk)
        .execute()
        .data
    )
    for o in od:
        opts[o["question_id"]].append({"option_index": o["option_index"], "body": o["body"]})

export = []
status = Counter()
fmt_live = Counter()
held = []
for r in rows:
    st = r["review_status"]
    status[st] += 1
    qopts = sorted(opts[r["id"]], key=lambda x: x["option_index"])
    export.append(
        {
            "q_no": r["q_no"],
            "body": r["body"] or "",
            "format": r["format"],
            "numerical_answer": r["numerical_answer"],
            "review_status": st,
            "correct_option": r["correct_option"],
            "question_options": qopts,
        }
    )
    if st in ("auto_ok", "human_ok"):
        fmt_live[r["format"]] += 1
    else:
        held.append(r["q_no"])

out = Path("out-math/agents/chapter_17/live_dump.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
print("chapter_id", cid)
print("total", len(rows))
print("status", dict(status))
print("live formats", dict(fmt_live))
print("held q_nos", held)
print("wrote", out)
