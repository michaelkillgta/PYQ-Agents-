#!/usr/bin/env python3
"""Crop every held Definite Integration question (with column wrap) to PNG."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import configure_book, load_skeleton
from repair_held_pyq import crop_png

CHAPTER_NO = 17
HELD = [
    9, 10, 17, 19, 20, 22, 29, 30, 31, 32, 42, 48, 59, 66, 73, 79, 85, 103,
    105, 112, 113, 119, 132, 133, 134, 140, 144, 145, 146, 147, 148, 149, 150,
    151, 152, 153, 154, 155, 165, 167, 169, 170, 173, 181, 182, 186, 199, 205,
    206, 207, 209, 224,
]

configure_book("math")
book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER_NO}
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_19/repair")
out.mkdir(parents=True, exist_ok=True)

for q in HELD:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q} -> {dest} ({dest.stat().st_size} bytes)", flush=True)
print(f"done {len(HELD)} crops")
