#!/usr/bin/env python3
"""Promote Three Dimensional Geometry (PDF ch 33) repairs to human_ok. Held must become 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.katex_check import is_solver_dump

p.configure_book("math")
REPAIRS = json.loads(Path("out-math/agents/chapter_33/repairs.json").read_text(encoding="utf-8"))

sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 33, "Mathematics")
rows = (
    sb.table("pyq_questions")
    .select("id,q_no,review_status,format,correct_option,numerical_answer")
    .eq("chapter_id", cid)
    .order("q_no")
    .execute()
    .data
)
q_by_no = {r["q_no"]: r for r in rows}
print(f"Loaded {len(rows)} questions from DB for chapter 33 (ID {cid}).")

for q_s, data in sorted(REPAIRS.items(), key=lambda kv: int(kv[0])):
    q_no = int(q_s)
    row = q_by_no.get(q_no)
    if not row:
        print(f"ERROR: Q{q_no} not found in DB!")
        continue
    qid = row["id"]
    fmt = data["format"]
    body = data["body"].strip()
    opts = data.get("options")
    corr_opt = data.get("correct_option")
    num_ans = data.get("numerical_answer")
    patch = {
        "format": fmt,
        "body": body,
        "review_status": "human_ok",
        "extraction_confidence": 1.0,
        "correct_option": corr_opt,
        "numerical_answer": num_ans,
    }
    sb.table("pyq_questions").update(patch).eq("id", qid).execute()
    sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
    if fmt == "mcq" and opts:
        opt_rows = [
            {"question_id": qid, "option_index": i, "body": opt_text.strip()}
            for i, opt_text in enumerate(opts, start=1)
        ]
        sb.table("pyq_question_options").insert(opt_rows).execute()
    print(f"Repaired and promoted Q{q_no:3d} [{fmt:9s}]: key={num_ans if fmt == 'numerical' else corr_opt}")

parsed_path = p.OUT / "agents" / "chapter_33" / "parsed.json"
if parsed_path.exists():
    parsed_disk = json.loads(parsed_path.read_text(encoding="utf-8"))
else:
    parsed_disk = {}
for q_s, data in REPAIRS.items():
    parsed_disk[q_s] = {
        "body": data["body"],
        "options": data.get("options"),
        "page": parsed_disk.get(q_s, {}).get("page"),
    }
parsed_path.write_text(json.dumps(parsed_disk, ensure_ascii=False, indent=1), encoding="utf-8")
print("Updated out-math/agents/chapter_33/parsed.json")

hold_path = p.OUT / "agents" / "chapter_33" / "hold.json"
hold_path.write_text(json.dumps({"chapter_no": 33, "holds": []}, indent=1), encoding="utf-8")
print("Updated out-math/agents/chapter_33/hold.json -> 0 holds")

print("\n--- Running full DB verification after promotion ---")
all_res = (
    sb.table("pyq_questions")
    .select(
        "id,q_no,review_status,format,correct_option,numerical_answer,body,"
        "pyq_question_options(option_index,body)"
    )
    .eq("chapter_id", cid)
    .order("q_no")
    .execute()
    .data
)

status_dist = {}
live_cnt = 0
held_cnt = 0
failures = []
for r in all_res:
    st = r["review_status"]
    status_dist[st] = status_dist.get(st, 0) + 1
    if st in ("auto_ok", "human_ok"):
        live_cnt += 1
    else:
        held_cnt += 1
    q = r["q_no"]
    fmt = r["format"]
    b = (r["body"] or "").strip()
    opts = sorted(r.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    if not b or b.startswith("(OCR missed") or is_solver_dump(b):
        failures.append((q, "bad_body", b[:60]))
    if fmt == "numerical":
        if not (r.get("numerical_answer") or "").strip():
            failures.append((q, "missing_num_ans", None))
    elif fmt == "mcq":
        if r.get("correct_option") not in (1, 2, 3, 4):
            failures.append((q, "bad_correct_option", r.get("correct_option")))
        if len(opts) != 4 or any(not (o.get("body") or "").strip() for o in opts):
            failures.append((q, "invalid_mcq_options", len(opts)))

total_cnt = len(all_res)
print("Final DB State for Chapter 33 (Three Dimensional Geometry):")
print(f"  Total Questions: {total_cnt}")
print(f"  Live (auto_ok/human_ok): {live_cnt} ({100 * live_cnt / total_cnt:.1f}%)")
print(f"  Held (unreviewed): {held_cnt}")
print(f"  Status distribution: {status_dist}")
print(f"  Validation failures: {len(failures)}")
if failures:
    for item in failures:
        print(f"    FAIL: {item}")
    sys.exit(1)
print("  ALL QUESTIONS STRICTLY PASS isPyqPaperFilled shape checks.")
if held_cnt != 0:
    sys.exit(2)
