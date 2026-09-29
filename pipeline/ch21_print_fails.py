#!/usr/bin/env python3
"""Print DE fill-gate fail bodies so we can transcribe from paper."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FAILS = [
    25, 31, 36, 39, 41, 42, 43, 44, 46, 53, 54, 56, 69, 82, 91, 98, 100,
    105, 111, 115, 146, 152, 153, 154, 156, 159, 160, 175, 178, 185, 195,
]
rows = {r["q_no"]: r for r in json.loads(Path("out-math/agents/chapter_21/live_dump.json").read_text(encoding="utf-8"))}
for q in FAILS:
    r = rows[q]
    body = r["body"]
    tail = body[-50:].replace("\n", " ")
    opts = r["question_options"]
    print("=" * 60)
    print(f"Q{q} fmt={r['format']} key={r['correct_option']}/{r['numerical_answer']} n_opts={len(opts)}")
    print("TAIL:", repr(tail))
    print("BODY:", body)
    for o in opts:
        print(f"  ({o['option_index']})", o["body"])
