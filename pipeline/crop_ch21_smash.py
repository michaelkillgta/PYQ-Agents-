#!/usr/bin/env python3
"""Crop clearly smashed DE live rows (truncated √ / broken KaTeX)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton, load_answer_key
from repair_held_pyq import crop_png

QS = [18, 101, 109, 120, 128, 139, 157, 183, 196]
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == 21}
key = load_answer_key().get("21", {}).get("answers", {})
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_21/smash")
out.mkdir(parents=True, exist_ok=True)
for q in QS:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q} page={specs[q]['page']} type={specs[q].get('answer_type')} key={key.get(str(q))}", flush=True)
