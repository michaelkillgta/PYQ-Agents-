#!/usr/bin/env python3
"""Crop DE fill-gate fails for paper transcription."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton, load_answer_key
from repair_held_pyq import crop_png

FAILS = [
    25, 31, 36, 39, 41, 42, 43, 44, 46, 53, 54, 56, 69, 82, 91, 98, 100,
    105, 111, 115, 146, 152, 153, 154, 156, 159, 160, 175, 178, 185, 195,
]
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == 21}
key = load_answer_key().get("21", {}).get("answers", {})
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_21/fillgate")
out.mkdir(parents=True, exist_ok=True)
meta = []
for q in FAILS:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    k = key.get(str(q), {})
    spec = specs[q]
    meta.append({"q_no": q, "page": spec["page"], "answer_type": spec.get("answer_type"), "key": k})
    print(f"cropped Q{q} page={spec['page']} type={spec.get('answer_type')} key={k}", flush=True)
Path("out-math/agents/chapter_21/fillgate_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
print(f"done {len(FAILS)}")
