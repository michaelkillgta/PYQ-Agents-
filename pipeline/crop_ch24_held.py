#!/usr/bin/env python3
"""Crop every held Parabola question (with column wrap) to PNG."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import configure_book, load_skeleton
from repair_held_pyq import crop_png

CHAPTER_NO = 24
HELD = [
    11, 12, 13, 14, 15, 16, 17, 18, 19, 29, 33, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
    69, 70, 71, 72, 73, 74, 75, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
    99, 100, 101, 102, 103, 104,
]

configure_book("math")
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER_NO}
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_24/repair")
out.mkdir(parents=True, exist_ok=True)

for q in HELD:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q} -> {dest} ({dest.stat().st_size} bytes)", flush=True)
print(f"done {len(HELD)} crops")
