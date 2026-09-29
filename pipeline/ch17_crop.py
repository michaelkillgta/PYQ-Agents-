#!/usr/bin/env python3
"""Crop Application of Derivatives (ch17) questions. Pass q_nos as args, or --held."""
from __future__ import annotations
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton, load_answer_key, supabase_client, resolve_chapter_id
from repair_held_pyq import crop_png

CHAPTER = 17
book = configure_book("math")
args = sys.argv[1:]
if not args:
    raise SystemExit("usage: ch17_crop.py --held | QNO...")

specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER}
key = load_answer_key().get(str(CHAPTER), {}).get("answers", {}) or load_answer_key().get("17", {}).get("answers", {})
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_17/repair")
out.mkdir(parents=True, exist_ok=True)

if args == ["--held"]:
    sb = supabase_client()
    cid = resolve_chapter_id(sb, CHAPTER, "Mathematics")
    held_rows = (
        sb.table("pyq_questions")
        .select("q_no")
        .eq("chapter_id", cid)
        .eq("review_status", "unreviewed")
        .order("q_no")
        .execute()
        .data
    )
    qs = [int(r["q_no"]) for r in held_rows]
else:
    qs = [int(x) for x in args]

print(f"crop {len(qs)} questions", flush=True)
for q in qs:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    k = key.get(str(q), {})
    spec = specs[q]
    print(f"cropped Q{q} page={spec['page']} type={spec.get('answer_type')} key={k}", flush=True)
