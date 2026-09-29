#!/usr/bin/env python3
"""High-confidence leftover smash in AoD live dump."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(Path("out-math/agents/chapter_17/live_dump.json").read_text(encoding="utf-8"))

HEAD = re.compile(
    r"Tangents and Normals|Monotonicity|Maxima Minima|Mean Value Theorem|"
    r"Rate of Change|Approximations|Errors|"
    r"Application of Derivatives|"
    r"Q\d+\*|# # mi|"
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
    if re.search(r"Q\d+", body[8:]):
        reasons.append("merged")
    if re.search(r"²x|\$y = y\$\(x\)", blob):
        reasons.append("ocr")
    if reasons:
        flags.append(q)
        print(f"Q{q:3d} {reasons} | {body.replace(chr(10), ' ')[-120:]}")

print("COUNT", len(flags), flags)
