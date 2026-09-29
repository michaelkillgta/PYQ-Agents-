#!/usr/bin/env python3
"""Crop every held Circle question (with column wrap) to PNG."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import configure_book, load_skeleton
from repair_held_pyq import crop_png

CHAPTER_NO = 23
HELD = [
    4, 9, 11, 13, 15, 16, 17, 18, 19, 20, 24, 32, 35, 38, 39, 41, 44, 45, 47,
    48, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 71, 72, 73,
    74, 75, 76, 77, 86, 91, 96, 100, 105, 106, 107, 108, 109, 110, 111, 112,
    113, 114, 115, 116, 117, 118, 119,
]

configure_book("math")
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER_NO}
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_23/repair")
out.mkdir(parents=True, exist_ok=True)

for q in HELD:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q} -> {dest} ({dest.stat().st_size} bytes)")
