#!/usr/bin/env python3
"""Verify a small 3D Geometry held batch with Sarvam GLM against the official key."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.models import SOLVER_A
from run_chapter_agents import v2_json

SOLVER_SYSTEM = """Solve this JEE Main question.
Reply JSON {"answer":"..."} only.
MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units.
Do not explain."""


def official_answer(data: dict) -> str:
    if data["format"] == "numerical":
        return str(data["numerical_answer"]).strip()
    return str(data["correct_option"]).strip()


def solve_batch(q_nos: list[int], batch_name: str, repairs: dict) -> dict:
    p.configure_book("math")
    env = p.load_env()
    limiter = p.RateLimiter(18)
    results = {}
    for q in q_nos:
        data = repairs[str(q)]
        fmt = data["format"]
        body = data["body"]
        opts = data.get("options")
        key = official_answer(data)
        opt_lines = ""
        if opts:
            opt_lines = "\n".join(f"({i}) {o}" for i, o in enumerate(opts, start=1))
        user_prompt = f"Type: {fmt}\nStem:\n{body}\n{opt_lines}\n"
        messages = [
            {"role": "system", "content": SOLVER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        model_ans = ""
        for attempt in range(4):
            try:
                resp = v2_json(SOLVER_A, messages, env, limiter)
                model_ans = str(resp.get("answer", "")).strip()
                if model_ans:
                    break
            except Exception as exc:
                model_ans = f"ERROR: {exc}"
                time.sleep(2 * (attempt + 1))
        match = model_ans == key
        if not match and fmt == "numerical":
            try:
                match = abs(float(model_ans) - float(key)) < 1e-9
            except ValueError:
                match = False
        results[str(q)] = {"format": fmt, "key": key, "model": model_ans, "match": match}
        print(
            f"[{batch_name}] Q{q:3d} [{fmt:9s}] Key:{key:8s} GLM:{model_ans:12s} Match:{match}",
            flush=True,
        )
    dest = Path(f"out-math/agents/chapter_33/sarvam_{batch_name}.json")
    dest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    matched = sum(1 for r in results.values() if r["match"])
    print(f"[{batch_name}] {matched}/{len(results)} matched. Saved {dest}", flush=True)
    mismatches = [q for q, r in results.items() if not r["match"]]
    if mismatches:
        print(f"[{batch_name}] mismatches: {mismatches}", flush=True)
        sys.exit(2)
    return results
