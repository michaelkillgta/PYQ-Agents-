#!/usr/bin/env python3
"""Merge vision batches, apply paper-format overrides, write repairs.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from agents.katex_check import is_solver_dump, katex_render_ok
from audit_paper_text import flags_for
from pyq_common import configure_book, load_answer_key

configure_book("math")
ch_key = load_answer_key().get("24", {}).get("answers", {})

repairs: dict = {}
for name in ("b1", "b2", "b3", "b4", "b5", "b6", "b7"):
    path = Path(f"out-math/agents/chapter_24/transcribe_{name}.json")
    blob = json.loads(path.read_text(encoding="utf-8"))
    repairs.update(blob)

# Paper blanks that the skeleton tagged mcq.
FORCE_NUM = {
    "61": "4",
    "62": "2",
}

Q104 = {
    "format": "mcq",
    "body": "Let a tangent to the curve $y^{2} = 24x$ meet the curve $xy = 2$ at the points $A$ and $B$. Then the mid-points of such line segments $AB$ lie on a parabola with the",
    "options": [
        "directrix $4x = 3$",
        "directrix $4x = -3$",
        "Length of latus rectum $\\dfrac{3}{2}$",
        "Length of latus rectum $2$",
    ],
    "correct_option": 1,
    "numerical_answer": None,
}

for q_s, data in list(repairs.items()):
    k = ch_key.get(q_s, {})
    body = (data.get("body") or "").strip()
    # Drop leftover headings / dates / page numbers that vision may glue on.
    for junk in (
        "Tangent to Parabola",
        "Common Tangent",
        "Chord with given Middle Point",
        "Normal to Parabola",
        "Chord of Contact",
        "Pair of Tangents",
        "Properties of Tangent",
        "Locus",
        "CHAPTER 25",
        "Ellipse",
        "Coordinate Geometry",
        "Parabola",
    ):
        body = body.replace(junk, " ")
    body = " ".join(body.split())
    data["body"] = body
    if q_s in FORCE_NUM:
        data["format"] = "numerical"
        data["options"] = None
        data["correct_option"] = None
        data["numerical_answer"] = FORCE_NUM[q_s]
        continue
    if data.get("format") == "numerical" or not data.get("options"):
        data["format"] = "numerical"
        data["options"] = None
        data["correct_option"] = None
        data["numerical_answer"] = str(k.get("value") or data.get("numerical_answer") or "").strip()
    else:
        data["format"] = "mcq"
        data["correct_option"] = int(k["value"])
        data["numerical_answer"] = None
        opts = data.get("options") or []
        data["options"] = [str(o).strip() for o in opts]

repairs["104"] = Q104

out = Path("out-math/agents/chapter_24/repairs.json")
out.write_text(json.dumps(dict(sorted(repairs.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {out} n={len(repairs)}")

fail = []
for q_s, data in sorted(repairs.items(), key=lambda kv: int(kv[0])):
    q = int(q_s)
    body = (data["body"] or "").strip()
    fmt = data["format"]
    k = ch_key.get(str(q), {})
    key_val = str(k.get("value") or "").strip()
    if not body or body.startswith("(OCR missed"):
        fail.append((q, "empty_body"))
    if is_solver_dump(body):
        fail.append((q, "solver_dump"))
    b_flags = flags_for(body, is_option=False)
    if b_flags:
        fail.append((q, f"body_flags:{b_flags}"))
    if not katex_render_ok(body):
        fail.append((q, "body_katex_fail"))
    if fmt == "numerical":
        num = str(data.get("numerical_answer") or "").strip()
        if not num:
            fail.append((q, "missing_num"))
        if key_val and num != key_val and q not in (61, 62):
            fail.append((q, f"num_key {num} != {key_val}"))
        if data.get("options"):
            fail.append((q, "numerical_has_options"))
    else:
        opts = data.get("options") or []
        if len(opts) != 4 or any(not str(o).strip() for o in opts):
            fail.append((q, f"bad_opts:{opts}"))
        if data.get("correct_option") != int(key_val):
            fail.append((q, f"mcq_key {data.get('correct_option')} != {key_val}"))
        for i, o in enumerate(opts, 1):
            o_flags = flags_for(o, is_option=True)
            blocking = [f for f in o_flags if not str(f).startswith("empty")]
            if blocking:
                fail.append((q, f"opt{i}_flags:{blocking}"))
            if not katex_render_ok(o):
                fail.append((q, f"opt{i}_katex_fail:{o[:60]}"))

print(f"quality failures: {len(fail)}")
for item in fail:
    print(" ", item)
if fail:
    sys.exit(1)
print("ALL repairs pass KaTeX + paper-text + official-key shape.")
