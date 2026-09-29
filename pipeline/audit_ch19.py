#!/usr/bin/env python3
"""Audit Mathematics PDF chapter 19 (Definite Integration) against skeleton, answer key, and DB."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import (
    configure_book,
    load_answer_key,
    load_skeleton,
    resolve_chapter_id,
    supabase_client,
)
from agents.katex_check import is_solver_dump, katex_render_ok
from audit_paper_text import flags_for

CHAPTER_NO = 17

configure_book("math")
sb = supabase_client()
cid = resolve_chapter_id(sb, CHAPTER_NO, "Mathematics")

res = (
    sb.table("pyq_questions")
    .select(
        "id,q_no,review_status,format,correct_option,numerical_answer,source_page,body,"
        "pyq_question_options(option_index,body)"
    )
    .eq("chapter_id", cid)
    .order("q_no")
    .execute()
    .data
)

skel = load_skeleton()
key_book = load_answer_key()
ch_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == CHAPTER_NO}
ch_key = key_book.get(str(CHAPTER_NO), {}).get("answers", {})

db_nos = {r["q_no"] for r in res}
skel_nos = set(ch_skel)
key_nos = {int(k) for k in ch_key}

status_counts = Counter(r["review_status"] for r in res)
format_counts = Counter(r["format"] for r in res)
live = sum(1 for r in res if r["review_status"] in ("auto_ok", "human_ok"))
held = sum(1 for r in res if r["review_status"] not in ("auto_ok", "human_ok"))

print("=== SCOPE ===")
print(f"Chapter: Definite Integration | PDF ch {CHAPTER_NO} | catalog_slug=definite-integration | chapter_id={cid}")
print(f"Skeleton: {len(ch_skel)}  Answer-key: {len(ch_key)}  DB: {len(res)}")
print(f"Missing in DB vs skeleton: {sorted(skel_nos - db_nos)}")
print(f"Extra in DB vs skeleton: {sorted(db_nos - skel_nos)}")
print(f"Missing in key vs skeleton: {sorted(skel_nos - key_nos)}")
print(f"Status: {dict(status_counts)}")
print(f"Formats: {dict(format_counts)}")
print(f"Total={len(res)}  Live={live}  Held={held}")
print()

held_rows = [r for r in res if r["review_status"] not in ("auto_ok", "human_ok")]
print(f"=== HELD Q_NOS ({len(held_rows)}) ===")
print([r["q_no"] for r in held_rows])
print()

issues = []
held_dump = []
for r in res:
    q = r["q_no"]
    st = r["review_status"]
    fmt = r["format"]
    body = (r["body"] or "").strip()
    opts = sorted(r.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    k = ch_key.get(str(q), {})
    row_issues = []

    if not body:
        row_issues.append("empty_body")
    elif body.startswith("(OCR missed"):
        row_issues.append("ocr_missed_body")
    elif is_solver_dump(body):
        row_issues.append("solver_dump_body")

    b_flags = flags_for(body, is_option=False) if body else []
    if b_flags:
        row_issues.append(f"body_flags:{b_flags}")
    if body and not katex_render_ok(body):
        row_issues.append("body_katex_fail")

    sk = ch_skel.get(q, {})
    sk_type = sk.get("answer_type")
    if sk_type == "numerical" and fmt != "numerical":
        row_issues.append(f"format_mismatch_skel={sk_type}_db={fmt}")
    if sk_type == "mcq" and fmt != "mcq":
        row_issues.append(f"format_mismatch_skel={sk_type}_db={fmt}")

    if fmt == "numerical":
        num_ans = r.get("numerical_answer")
        if not num_ans or not str(num_ans).strip():
            row_issues.append("missing_numerical_answer")
        key_val = str(k.get("value") or "").strip()
        if key_val and str(num_ans or "").strip() != key_val:
            row_issues.append(f"num_key_mismatch_db={num_ans}_key={key_val}")
    elif fmt == "mcq":
        corr_opt = r.get("correct_option")
        if corr_opt not in (1, 2, 3, 4):
            row_issues.append(f"bad_correct_option:{corr_opt}")
        key_val = str(k.get("value") or "").strip()
        if key_val and str(corr_opt) != key_val:
            row_issues.append(f"mcq_key_mismatch_db={corr_opt}_key={key_val}")
        if len(opts) != 4:
            row_issues.append(f"opt_count_{len(opts)}")
        for o in opts:
            obody = (o.get("body") or "").strip()
            if not obody:
                row_issues.append(f"opt_{o.get('option_index')}_empty")
            else:
                o_flags = flags_for(obody, is_option=True)
                blocking = [f for f in o_flags if not f.startswith("empty")]
                if blocking:
                    row_issues.append(f"opt_{o.get('option_index')}_flags:{blocking}")
                if not katex_render_ok(obody):
                    row_issues.append(f"opt_{o.get('option_index')}_katex_fail")
    else:
        row_issues.append(f"unexpected_format:{fmt}")

    for iss in row_issues:
        issues.append((q, st, iss))

    if st not in ("auto_ok", "human_ok"):
        held_dump.append(
            {
                "q_no": q,
                "status": st,
                "format": fmt,
                "page": r.get("source_page"),
                "skel_type": sk_type,
                "key": k,
                "correct_option": r.get("correct_option"),
                "numerical_answer": r.get("numerical_answer"),
                "body": body,
                "options": [(o.get("option_index"), o.get("body")) for o in opts],
                "issues": row_issues,
                "figure_keys": sk.get("figure_keys") or [],
            }
        )

print(f"=== ISSUE REPORTS ({len(issues)}) ===")
by_status = Counter(st for _, st, _ in issues)
print(f"By status: {dict(by_status)}")
held_issues = [(q, st, iss) for q, st, iss in issues if st not in ("auto_ok", "human_ok")]
live_issues = [(q, st, iss) for q, st, iss in issues if st in ("auto_ok", "human_ok")]
print(f"Held issues: {len(held_issues)}  Live issues: {len(live_issues)}")
print("\n-- HELD --")
for q, st, iss in held_issues:
    print(f"  Q{q:3d} [{st:10s}] -> {iss}")
if live_issues:
    print("\n-- LIVE --")
    for q, st, iss in live_issues:
        print(f"  Q{q:3d} [{st:10s}] -> {iss}")

out_path = Path("out-math/agents/chapter_19/held_audit.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(held_dump, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nWrote {out_path} ({len(held_dump)} held rows)")
