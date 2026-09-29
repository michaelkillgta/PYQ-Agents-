#!/usr/bin/env python3
"""High-confidence leftover smash in DE live dump (ignore good KaTeX)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(Path("out-math/agents/chapter_21/live_dump.json").read_text(encoding="utf-8"))

HEAD = re.compile(
    r"Formation of Differential|Variable Separable|Exact Forms|Applications of DE|"
    r"Linear Differential|Q\d+\*|# # mi|"
    r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
    re.I,
)
GLYPH = re.compile(r"[√ₑʸᵈˣ¹₆]|eˣ|eʸ")
TRUNC = re.compile(r"(?:\by\s*$|\by\($|intersect at\s*$|, y$)")


def dollars_ok(s: str) -> bool:
    return s.count("$") % 2 == 0


flags = []
for r in rows:
    q = int(r["q_no"])
    body = r["body"] or ""
    opts = [o["body"] or "" for o in r["question_options"]]
    blob = body + "\n" + "\n".join(opts)
    reasons = []
    if HEAD.search(blob):
        reasons.append("heading")
    if GLYPH.search(blob):
        reasons.append("glyph")
    if not dollars_ok(body) or any(not dollars_ok(o) for o in opts):
        reasons.append("$")
    if TRUNC.search(body.strip()) or body.strip().endswith(" y") or body.rstrip().endswith(", y"):
        reasons.append("trunc")
    if any(
        o.strip() in {"y", "= e¹/2 - 1", ")ₑ 2", "ₑ 2", "ₑ 9", "ₑ 18"}
        or "ₑ" in o
        or o.strip().endswith(" Form")
        or o.strip().endswith(" DE")
        for o in opts
    ):
        reasons.append("opt")
    if re.search(r"Q\d+", body[8:]):
        reasons.append("merged")
    if reasons:
        flags.append(q)
        print(f"Q{q:3d} {reasons} | {body.replace(chr(10), ' ')[-100:]}")

print("COUNT", len(flags), flags)
