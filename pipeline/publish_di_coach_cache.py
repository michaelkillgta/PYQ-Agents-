#!/usr/bin/env python3
"""Publish cached DI coach JSON; repair the two glm failures; write to Supabase."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pyq_common as p
from agents.models import PRIMARY_SOLVER
from generate_di_coach import (
    CACHE,
    CHAPTER_NO,
    SUBJECT,
    SYSTEM,
    YEARS_DEFAULT,
    ask,
    dump,
    fetch_rows,
    paper_solution,
    validate,
)

Q114 = "f0d3501b-eeab-4341-9e38-18aa03aa2608"
Q154 = "3dd71419-4646-4bab-960b-9d1fbe809de0"

Q114_FORMULAS = [
    {
        "name": "x to -x on symmetric limits",
        "tex": r"\int_{-a}^{a} f(x)\,dx = \int_{-a}^{a} f(-x)\,dx",
        "note": "Add original and flipped integrands.",
    },
    {
        "name": "Reciprocal exponential pair",
        "tex": r"\frac{1}{1+k^{t}}+\frac{1}{1+k^{-t}}=1",
        "note": "Cancels the two special denominators.",
    },
    {
        "name": "Even function property",
        "tex": r"\int_{-a}^{a} f(x)\,dx = 2\int_{0}^{a} f(x)\,dx",
        "note": "Use after the pair cancels.",
    },
    {
        "name": "Sine-square identity",
        "tex": r"\sin^2 x=\frac{1-\cos 2x}{2}",
        "note": "Integrate the leftover even pieces.",
    },
]


def load_valid() -> dict[str, dict]:
    got: dict[str, dict] = {}
    for path in CACHE.glob("*.json"):
        qid = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        parsed = validate(data)
        if not parsed:
            continue
        tips, formulas = parsed
        got[qid] = {"id": qid, "tips": tips, "formulas": formulas}
    return got


def repair_q114(got: dict[str, dict]) -> None:
    path = CACHE / f"{Q114}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["formulas"] = Q114_FORMULAS
    parsed = validate(data)
    if not parsed:
        raise SystemExit("q114 still invalid after formula repair")
    dump(path, data)
    tips, formulas = parsed
    got[Q114] = {"id": Q114, "tips": tips, "formulas": formulas}


def repair_q154(sb, env, limiter, got: dict[str, dict]) -> None:
    cache = CACHE / f"{Q154}.json"
    if cache.is_file():
        cache.unlink()
    rows = fetch_rows(sb, p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT), YEARS_DEFAULT)
    row = next(r for r in rows if r["id"] == Q154)
    rec = ask(row, env, limiter)
    got[Q154] = rec


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    got = load_valid()
    print(f"valid cache {len(got)}", flush=True)
    repair_q114(got)
    print("repaired q114", flush=True)
    limiter = p.RateLimiter()
    try:
        repair_q154(sb, env, limiter, got)
        print(
            f"repaired q154 tips={len(got[Q154]['tips'])} formulas={len(got[Q154]['formulas'])}",
            flush=True,
        )
    except Exception as exc:
        print(f"q154 glm fail {exc}", flush=True)
        return 1
    cid = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    want = {r["id"] for r in fetch_rows(sb, cid, YEARS_DEFAULT)}
    publish = [rec for rec in got.values() if rec["id"] in want]
    for rec in publish:
        sb.table("pyq_questions").update({
            "tips_md": json.dumps({"tips": rec["tips"]}, ensure_ascii=False),
            "formulas_md": json.dumps({"formulas": rec["formulas"]}, ensure_ascii=False),
        }).eq("id", rec["id"]).execute()
    print(f"published {len(publish)}", flush=True)
    missing = sorted(want - {rec["id"] for rec in publish})
    if missing:
        print("missing", missing, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
