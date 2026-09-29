#!/usr/bin/env python3
"""Crop leftover DE smash (pass q_nos as args)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton, load_answer_key
from repair_held_pyq import crop_png

QS = [int(x) for x in sys.argv[1:]]
if not QS:
    raise SystemExit("usage: ch21_crop.py QNO...")
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
