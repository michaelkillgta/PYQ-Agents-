#!/usr/bin/env python3
"""Verify Circle (ch 23) repairs with Sarvam GLM against the official key."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.models import SOLVER_A
from run_chapter_agents import v2_json

p.configure_book("math")
env = p.load_env()
limiter = p.RateLimiter(60)
key_book = p.load_answer_key()
ch_key = key_book.get("23", {}).get("answers", {})
REPAIRS = json.loads(Path("out-math/agents/chapter_23/repairs.json").read_text(encoding="utf-8"))

SOLVER_SYSTEM = """Solve this JEE Main question.
Reply JSON {"answer":"..."} only.
MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units.
Do not explain."""


def official_answer(q_no: int, data: dict) -> str:
    if data["format"] == "numerical":
        return str(data["numerical_answer"]).strip()
    return str(data["correct_option"]).strip()


def solve_one(item):
    q_s, data = item
    q_no = int(q_s)
    fmt = data["format"]
    body = data["body"]
    opts = data.get("options")
    key = official_answer(q_no, data)
    opt_lines = ""
    if opts:
        opt_lines = "\n".join(f"({i}) {o}" for i, o in enumerate(opts, start=1))
    user_prompt = f"Type: {fmt}\nStem:\n{body}\n{opt_lines}\n"
    messages = [
        {"role": "system", "content": SOLVER_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    try:
        resp = v2_json(SOLVER_A, messages, env, limiter)
        model_ans = str(resp.get("answer", "")).strip()
    except Exception as exc:
        model_ans = f"ERROR: {exc}"
    match = model_ans == key
    if not match and fmt == "numerical":
        try:
            match = float(model_ans) == float(key)
        except ValueError:
            match = False
    return q_no, {"format": fmt, "key": key, "model": model_ans, "match": match}


results = {}
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(solve_one, item) for item in REPAIRS.items()]
    for fut in as_completed(futures):
        q_no, res = fut.result()
        results[q_no] = res
        print(
            f"Q{q_no:3d} [{res['format']:9s}] -> Key: {res['key']:8s} | GLM: {res['model']:12s} | Match: {res['match']}",
            flush=True,
        )

out = Path("out-math/agents/chapter_23/sarvam_verification.json")
out.write_text(json.dumps({str(k): v for k, v in sorted(results.items())}, indent=2), encoding="utf-8")
matched = sum(1 for r in results.values() if r["match"])
print(f"\n{matched}/{len(results)} matched official key. Saved {out}")
mismatches = [q for q, r in sorted(results.items()) if not r["match"]]
if mismatches:
    print("Mismatches:", mismatches)
    sys.exit(2)
print("ALL held questions match the official MathonGo / NTA key.")
