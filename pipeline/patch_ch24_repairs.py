#!/usr/bin/env python3
"""Patch known Parabola repair defects, then re-run KaTeX gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from agents.katex_check import is_solver_dump, katex_render_ok
from audit_paper_text import flags_for

path = Path("out-math/agents/chapter_24/repairs.json")
repairs = json.loads(path.read_text(encoding="utf-8"))

repairs["11"]["body"] = (
    "The sum of diameters of the circles that touch (i) the parabola "
    "$75x^{2} = 64(5y - 3)$ at the point $\\left(\\dfrac{8}{5}, \\dfrac{6}{5}\\right)$ "
    "and (ii) the $y$-axis, is equal to _________."
)
repairs["59"]["options"][1] = "$\\dfrac{88}{5}$"
repairs["88"]["body"] = (
    "A line passing through the point $A(-2, 0)$, touches the parabola "
    "$P : y^{2} = x - 2$ at the point $B$ in the first quadrant. The area of the "
    "region bounded by the line $AB$, parabola $P$ and the $x$-axis, is"
)
repairs["89"]["body"] = (
    "Let $r$ be the radius of the circle, which touches the $x$-axis at the point "
    "$(a, 0)$, $a < 0$ and the parabola $y^{2} = 9x$ at the point $(4, 6)$. "
    "Then $r$ is equal to _________."
)
repairs["93"]["body"] = (
    "Let $S$ be the set of all $a \\in \\mathbb{N}$ such that the area of the "
    "triangle formed by the tangent at the point $P(b, c)$, $b, c \\in \\mathbb{N}$, "
    "on the parabola $y^{2} = 2ax$ and the lines $x = b$, $y = 0$ is $16$ unit$^{2}$, "
    "then $\\sum_{a \\in S} a$ is equal to _________."
)

for rec in repairs.values():
    rec.pop("page", None)
    rec.pop("error", None)

path.write_text(json.dumps(repairs, ensure_ascii=False, indent=2), encoding="utf-8")

fail = []
for q_s, data in sorted(repairs.items(), key=lambda kv: int(kv[0])):
    q = int(q_s)
    body = data["body"]
    if not body or is_solver_dump(body):
        fail.append((q, "bad_body"))
    if flags_for(body, is_option=False):
        fail.append((q, flags_for(body, is_option=False)))
    if not katex_render_ok(body):
        fail.append((q, "body_katex_fail"))
    if data["format"] == "mcq":
        for i, o in enumerate(data["options"], 1):
            if not katex_render_ok(o):
                fail.append((q, f"opt{i}_katex"))
print("failures", fail)
if fail:
    sys.exit(1)
print("patched repairs OK", len(repairs))
