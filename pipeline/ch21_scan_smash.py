#!/usr/bin/env python3
"""Find smashed DE options/stems that still pass fill-gate."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(Path("out-math/agents/chapter_21/live_dump.json").read_text(encoding="utf-8"))
pat = re.compile(r"(√|\\sqrt)\s*$|^\s*[\(\[]?\s*(√|\\sqrt)|eʸ|ᵈʸ|π/√")
for r in rows:
    hits = []
    if pat.search(r["body"] or ""):
        hits.append("BODY " + (r["body"][-80:]).replace("\n", " "))
    for o in r["question_options"]:
        b = o["body"] or ""
        if pat.search(b) or len(b) < 2:
            hits.append(f"opt{o['option_index']} {b!r}")
    if hits:
        print(f"Q{r['q_no']} {r['format']}")
        for h in hits:
            print(" ", h)
