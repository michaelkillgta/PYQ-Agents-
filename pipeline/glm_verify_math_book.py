#!/usr/bin/env python3
"""GLM 5.3 vs PDF key for every live Maths PYQ. Resume-safe. Never overwrite keys.

Also asks whether the four printed options look complete (no next-question bleed).

    python glm_verify_math_book.py
    python glm_verify_math_book.py --chapter 2
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.models import PRIMARY_SOLVER
from agents.solvers import matches_pdf_key
from run_chapter_agents import v2_json

SOLVER_SYSTEM = """You check one JEE Main question as printed.
Reply JSON only:
{"answer":"...","options_ok":true,"issue":""}
Rules:
- MCQ: answer is 1, 2, 3, or 4 (the printed option that is correct).
- Numerical: answer is the number only, no units.
- options_ok is false if an option is empty, truncated, a heading, a page number,
  solver talk, or clearly the next question's stem glued on.
- issue is "" when options_ok is true; else one of empty|bleed|truncated|heading|order.
Do not explain."""

OUT_DIR = Path("out-math/glm_option_audit")


def fetch_chapter_rows(sb, chapter_id: str) -> list[dict]:
    out: list[dict] = []
    start = 0
    while True:
        chunk = (
            sb.table("pyq_questions")
            .select(
                "id,q_no,format,correct_option,numerical_answer,body,"
                "pyq_question_options(option_index,body)"
            )
            .eq("chapter_id", chapter_id)
            .order("q_no")
            .range(start, start + 999)
            .execute()
            .data
        )
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 1000:
            break
        start += 1000
    return out


def cache_path(chapter_no: int, q_no: int) -> Path:
    return OUT_DIR / f"ch{chapter_no:02d}" / f"q{q_no:03d}.json"


def solve_one(chapter_no: int, row: dict, pdf_key: dict, env: dict, limiter: p.RateLimiter) -> dict:
    q_no = int(row["q_no"])
    path = cache_path(chapter_no, q_no)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    opts = sorted(row.get("pyq_question_options") or [], key=lambda o: o.get("option_index") or 0)
    opt_lines = "\n".join(
        f"({o['option_index']}) {o.get('body') or ''}" for o in opts
    )
    fmt = row.get("format") or pdf_key.get("type")
    user = (
        f"Type: {fmt}\n"
        f"Stem:\n{row.get('body') or ''}\n"
        f"{opt_lines}\n"
    )
    messages = [
        {"role": "system", "content": SOLVER_SYSTEM},
        {"role": "user", "content": user},
    ]
    rec = {
        "chapter_no": chapter_no,
        "q_no": q_no,
        "format": fmt,
        "pdf_key": str(pdf_key.get("value") or ""),
        "pdf_type": pdf_key.get("type"),
        "glm": None,
        "options_ok": None,
        "issue": None,
        "match": False,
        "error": None,
    }
    try:
        data = v2_json(PRIMARY_SOLVER, messages, env, limiter)
        rec["glm"] = str(data.get("answer") or "").strip()
        rec["options_ok"] = data.get("options_ok")
        rec["issue"] = data.get("issue") or ""
        rec["match"] = matches_pdf_key(
            rec["glm"], str(pdf_key.get("type") or fmt), str(pdf_key.get("value") or "")
        )
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def run_chapter(chapter_no: int, sb, key_book: dict, env: dict, limiter: p.RateLimiter) -> dict:
    ch = (
        sb.table("pyq_chapters")
        .select("id,name")
        .eq("unit_id", 3)
        .eq("chapter_no", chapter_no)
        .limit(1)
        .execute()
        .data
    )
    if not ch:
        raise SystemExit(f"no maths chapter {chapter_no}")
    rows = fetch_chapter_rows(sb, ch[0]["id"])
    answers = (key_book.get(str(chapter_no)) or {}).get("answers") or {}
    summary = {
        "chapter_no": chapter_no,
        "name": ch[0]["name"],
        "n": len(rows),
        "match": 0,
        "mismatch": 0,
        "options_bad": 0,
        "error": 0,
        "mismatches": [],
        "options_flags": [],
    }
    jobs = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in rows:
            k = answers.get(str(int(row["q_no"]))) or {}
            jobs.append(pool.submit(solve_one, chapter_no, row, k, env, limiter))
        for fut in as_completed(jobs):
            rec = fut.result()
            if rec.get("error"):
                summary["error"] += 1
            elif rec.get("match"):
                summary["match"] += 1
            else:
                summary["mismatch"] += 1
                summary["mismatches"].append(rec["q_no"])
            if rec.get("options_ok") is False:
                summary["options_bad"] += 1
                summary["options_flags"].append({"q_no": rec["q_no"], "issue": rec.get("issue")})
            status = "ok" if rec.get("match") and rec.get("options_ok") is not False else "flag"
            print(
                f"ch{chapter_no} Q{rec['q_no']:3d} {status} "
                f"pdf={rec.get('pdf_key')} glm={rec.get('glm')} "
                f"opts_ok={rec.get('options_ok')} {rec.get('error') or rec.get('issue') or ''}",
                flush=True,
            )
    dest = OUT_DIR / f"chapter_{chapter_no:02d}_summary.json"
    dest.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"ch{chapter_no} done n={summary['n']} match={summary['match']} "
        f"mismatch={summary['mismatch']} options_bad={summary['options_bad']} "
        f"error={summary['error']}",
        flush=True,
    )
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    args = ap.parse_args()
    p.configure_book("math")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    env = p.load_env()
    limiter = p.RateLimiter(48)
    sb = p.supabase_client()
    key_book = p.load_answer_key()
    chapters = [args.chapter] if args.chapter else list(range(1, 34))
    book = {"chapters": []}
    for n in chapters:
        book["chapters"].append(run_chapter(n, sb, key_book, env, limiter))
    (OUT_DIR / "BOOK_SUMMARY.json").write_text(
        json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
