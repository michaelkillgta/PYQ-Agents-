#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from pyq_common import configure_book, load_skeleton
from repair_held_pyq import crop_png

book = configure_book("math")
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == 23}
pdf = Path(book["pdf"])
out = Path("out-math/agents/chapter_23/repair")
for q in [10, 25, 36, 37, 40, 67, 99, 120, 126]:
    dest = out / f"q{q:03d}.png"
    crop_png(pdf, specs[q], dest, specs)
    print(f"cropped Q{q}")
