#!/usr/bin/env python3
"""Tighter leftover smash scan for AoD live dump."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(Path("out-math/agents/chapter_17/live_dump.json").read_text(encoding="utf-8"))

HEAD = re.compile(
    r"Tangent Normal|Tangents and Normals|Monotonicity|Maxima Minima|"
    r"Mean Value Theorem|ADVANCED STYLE|Rate of Change|"
    r"Application of Derivatives|MUST DO|CONCEPT BUILDER",
    re.I,
)
DATE = re.compile(r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", re.I)
GLYPH = re.compile(r"[√ₑʸᵈˣ₁-₉⁰-⁹]|eˣ|eʸ|ₓ")
OPT_NUM = re.compile(r"^\s*\(\s*[1-4]\s*\)")
BAD = re.compile(r"mathongo|# # mi|\\hfill|Q\d+\*")


def dollars_ok(s: str) -> bool:
    return s.count("$") % 2 == 0


flags = []
for r in rows:
    q = int(r["q_no"])
    body = r["body"] or ""
    opts = [o["body"] or "" for o in r["question_options"]]
    blob = body + "\n" + "\n".join(opts)
    reasons = []
    if HEAD.search(blob) and not re.search(r"mean value theorem|Rolle", body, re.I):
        reasons.append("heading")
    if DATE.search(blob):
        reasons.append("date")
    if GLYPH.search(blob):
        reasons.append("glyph")
    if not dollars_ok(body) or any(not dollars_ok(o) for o in opts):
        reasons.append("$")
    if BAD.search(blob):
        reasons.append("ocr")
    if re.search(r"Q\d+", body[8:]):
        reasons.append("merged")
    if any(OPT_NUM.search(o) for o in opts):
        reasons.append("optnum")
    if r["format"] == "mcq" and len(opts) != 4:
        reasons.append("nopt")
    if r["format"] == "numerical" and r.get("numerical_answer") in (None, ""):
        reasons.append("nans")
    if reasons:
        flags.append(q)
        print(f"Q{q:3d} {reasons} | {body.replace(chr(10), ' ')[:140]}")

print("COUNT", len(flags), flags)
