#!/usr/bin/env python3
"""Strip leftover (1)-(4) prefixes from AoD MCQ options (dump-driven)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from ch17_push import push_repairs

sys.stdout.reconfigure(encoding="utf-8")
PREFIX = re.compile(r"^\s*\(\s*[1-4]\s*\)\s*")
SKIP = {66, 76, 140, 168, 173, 64, 2, 36, 133, 134, 135, 139, 158}
rows = json.loads(Path("out-math/agents/chapter_17/live_dump.json").read_text(encoding="utf-8"))
want = {int(x) for x in sys.argv[1:]}
repairs = {}
for r in rows:
    q = int(r["q_no"])
    if q in SKIP:
        continue
    if want and q not in want:
        continue
    opts = [o["body"] or "" for o in sorted(r["question_options"], key=lambda o: o["option_index"])]
    if r["format"] != "mcq" or len(opts) != 4:
        continue
    if not any(PREFIX.search(o) for o in opts):
        continue
    stripped = [PREFIX.sub("", o).strip() for o in opts]
    repairs[q] = {
        "format": "mcq",
        "body": r["body"],
        "options": stripped,
        "correct_option": r["correct_option"],
        "numerical_answer": None,
    }
print(f"stripping {sorted(repairs)}")
push_repairs(repairs)
