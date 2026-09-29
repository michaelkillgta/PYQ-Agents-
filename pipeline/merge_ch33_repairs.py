#!/usr/bin/env python3
"""Merge vision batches, apply paper-format overrides, write repairs.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from agents.katex_check import is_solver_dump, katex_render_ok
from audit_paper_text import flags_for
from pyq_common import configure_book, load_answer_key, load_skeleton

configure_book("math")
CHAPTER_NO = 33
ch_key = load_answer_key().get(str(CHAPTER_NO), {}).get("answers", {})
specs = {s["q_no"]: s for s in load_skeleton() if s.get("chapter_no") == CHAPTER_NO}

repairs: dict = {}
for name in ("b1", "b2", "b3", "b4", "b5", "b6", "b7"):
    path = Path(f"out-math/agents/chapter_33/transcribe_{name}.json")
    blob = json.loads(path.read_text(encoding="utf-8"))
    repairs.update(blob)

HEADING_JUNK = (
    "Three Dimensional Geometry",
    "3D Geometry",
    "Direction Cosines",
    "Direction Ratios",
    "Equation of Line",
    "Equation of Plane",
    "Angle between",
    "Shortest Distance",
    "Coplanar Lines",
    "MUST DO PROBLEMS",
    "CONCEPT BUILDER",
    "ADVANCED STYLE PROBLEMS",
    "ADVANCED",
    "CHAPTER 33",
    "CHAPTER 34",
    "Vector Algebra",
)

BLANK = re.compile(r"_{3,}|\.{3,}|…|\\dots")


def looks_numerical(body: str, spec: dict, opts) -> bool:
    if spec.get("answer_type") == "numerical":
        return True
    if BLANK.search(body or "") and not (
        isinstance(opts, list) and len(opts) == 4 and all(str(o).strip() for o in opts)
    ):
        return True
    return False


for q_s, data in list(repairs.items()):
    q = int(q_s)
    k = ch_key.get(q_s, {})
    spec = specs.get(q, {})
    body = (data.get("body") or "").strip()
    for junk in HEADING_JUNK:
        body = body.replace(junk, " ")
    body = " ".join(body.split())
    body = body.replace("\x07", "\\").replace("\x0c", "\\f")
    body = re.sub(r"(?<!\\)left\(", r"\\left(", body)
    body = re.sub(r"(?<!\\)right\)", r"\\right)", body)
    body = body.replace(" rac{", "\\frac{")
    data["body"] = body
    opts = data.get("options")
    if looks_numerical(body, spec, opts):
        data["format"] = "numerical"
        data["options"] = None
        data["correct_option"] = None
        data["numerical_answer"] = str(k.get("value") or data.get("numerical_answer") or "").strip()
        continue
    if data.get("format") == "numerical" or not opts:
        data["format"] = "numerical"
        data["options"] = None
        data["correct_option"] = None
        data["numerical_answer"] = str(k.get("value") or data.get("numerical_answer") or "").strip()
    else:
        data["format"] = "mcq"
        data["correct_option"] = int(k["value"]) if str(k.get("value", "")).isdigit() else data.get("correct_option")
        data["numerical_answer"] = None
        cleaned = []
        for o in opts:
            inner = str(o).strip().replace("\x07", "\\").replace("\x0c", "\\f").replace("$", "").strip()
            if re.search(r"\\[a-zA-Z]|[_^{]", inner):
                inner = f"${inner}$"
            cleaned.append(inner)
        data["options"] = cleaned

out = Path("out-math/agents/chapter_33/repairs.json")
out.write_text(
    json.dumps(dict(sorted(repairs.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
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
        if key_val and num != key_val:
            fail.append((q, f"num_key {num} != {key_val}"))
        if data.get("options"):
            fail.append((q, "numerical_has_options"))
    else:
        opts = data.get("options") or []
        if len(opts) != 4 or any(not str(o).strip() for o in opts):
            fail.append((q, f"bad_opts:{opts}"))
        if str(data.get("correct_option")) != key_val:
            fail.append((q, f"mcq_key {data.get('correct_option')} != {key_val}"))
        for i, o in enumerate(opts, 1):
            o_flags = [f for f in flags_for(o, is_option=True) if not str(f).startswith("empty")]
            if o_flags:
                fail.append((q, f"opt{i}_flags:{o_flags}"))
            if not katex_render_ok(o):
                fail.append((q, f"opt{i}_katex_fail:{o[:80]}"))

print(f"quality failures: {len(fail)}")
for item in fail:
    print(" ", item)
if fail:
    sys.exit(1)
print("ALL repairs pass KaTeX + paper-text + official-key shape.")
