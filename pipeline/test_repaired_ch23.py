#!/usr/bin/env python3
"""KaTeX + paper-text gate for Circle (ch 23) repairs before promotion."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from agents.katex_check import is_solver_dump, katex_render_ok
from audit_paper_text import flags_for
from pyq_common import configure_book, load_answer_key

configure_book("math")
REPAIRS = json.loads(Path("out-math/agents/chapter_23/repairs.json").read_text(encoding="utf-8"))
ch_key = load_answer_key().get("23", {}).get("answers", {})

fail = []
for q_s, data in sorted(REPAIRS.items(), key=lambda kv: int(kv[0])):
    q = int(q_s)
    body = (data["body"] or "").strip()
    fmt = data["format"]
    k = ch_key.get(str(q), {})
    key_val = str(k.get("value") or "").strip()

    if not body:
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
        if data.get("options") is not None:
            fail.append((q, "numerical_has_options"))
        if key_val and num != key_val:
            fail.append((q, f"num_key_mismatch {num} vs {key_val}"))
    elif fmt == "mcq":
        opts = data.get("options") or []
        if len(opts) != 4 or any(not str(o).strip() for o in opts):
            fail.append((q, f"bad_opts:{opts}"))
        corr = data.get("correct_option")
        if corr not in (1, 2, 3, 4):
            fail.append((q, f"bad_corr:{corr}"))
        if key_val and str(corr) != key_val:
            fail.append((q, f"mcq_key_mismatch {corr} vs {key_val}"))
        for i, o in enumerate(opts, 1):
            o_flags = [f for f in flags_for(o, is_option=True) if not f.startswith("empty")]
            if o_flags:
                fail.append((q, f"opt{i}_flags:{o_flags}"))
            if not katex_render_ok(o):
                fail.append((q, f"opt{i}_katex_fail:{o}"))
    else:
        fail.append((q, f"bad_format:{fmt}"))

print(f"Repairs: {len(REPAIRS)}")
print(f"Failures: {len(fail)}")
for item in fail:
    print(f"  FAIL Q{item[0]} -> {item[1]}")
if not fail:
    print("ALL 61 REPAIRS PASS KaTeX + paper-text + official-key checks.")
sys.exit(1 if fail else 0)
