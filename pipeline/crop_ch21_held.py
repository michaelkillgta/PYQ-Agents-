#!/usr/bin/env python3
"""Crop Differential Equations (ch 21) held questions."""
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton, load_answer_key, supabase_client, resolve_chapter_id
from repair_held_pyq import crop_png

CHAPTER = 21
book = configure_book("math")
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
held = [int(r["q_no"]) for r in held_rows]
print(f"held={held}")

specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER}
key = load_answer_key().get(str(CHAPTER), {}).get("answers", {})
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_21/repair")
out.mkdir(parents=True, exist_ok=True)
meta = []
for q in held:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    k = key.get(str(q), {})
    spec = specs[q]
    meta.append({
        "q_no": q,
        "page": spec["page"],
        "answer_type": spec.get("answer_type"),
        "key": k,
        "figure_keys": spec.get("figure_keys") or [],
    })
    print(f"cropped Q{q} page={spec['page']} type={spec.get('answer_type')} key={k}", flush=True)
Path("out-math/agents/chapter_21/held_meta.json").write_text(
    __import__("json").dumps(meta, indent=1), encoding="utf-8"
)
print(f"done {len(held)} crops")
