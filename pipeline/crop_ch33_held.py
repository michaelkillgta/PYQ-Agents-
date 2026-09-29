#!/usr/bin/env python3
"""Crop every held Three Dimensional Geometry question to PNG."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import configure_book, load_skeleton
from repair_held_pyq import crop_png

CHAPTER_NO = 33
HELD = [
    16, 23, 26, 29, 34, 37, 38, 42, 44, 51, 60, 61, 64, 72, 79, 82, 84, 92,
    98, 108, 112, 139, 144, 145, 154, 159, 160, 166, 173, 185, 186, 188, 206,
    208, 214, 233, 245, 246, 247, 252, 253, 262, 270, 276, 280, 298,
]

configure_book("math")
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER_NO}
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_33/repair")
out.mkdir(parents=True, exist_ok=True)

for q in HELD:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q} -> {dest} ({dest.stat().st_size} bytes)", flush=True)
print(f"done {len(HELD)} crops")
