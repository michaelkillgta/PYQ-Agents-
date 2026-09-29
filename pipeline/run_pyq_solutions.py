#!/usr/bin/env python3
"""Write Chapter PYQ worked solutions with glm5.3.

    python run_pyq_solutions.py --book math --chapter 19 --year 2026
    python run_pyq_solutions.py --book math --chapter 19 --whole-chapter

One worker per question. Vision (gemma4) only for figures. Never flash. Never Gemini.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

import pyq_common as p
from agents.models import assert_model_may_see_image
from agents.solutions import (
    SOLUTION_MODEL,
    SOLUTION_SYSTEM,
    VISION_DESCRIBE_MODEL,
    VISION_FIGURE_SYSTEM,
    assert_solution_model,
    combine_question_md,
    dump_worked_payload,
    jobs_for_scope,
    normalize_worked_payload,
    official_key,
    should_write_solution,
    solution_md_complete,
)

SELECT = (
    "id,q_no,tier,format,body,correct_option,numerical_answer,exam_date,"
    "review_status,solution_md,"
    "question_options:pyq_question_options(option_index,body),"
    "figure_links:pyq_figure_links(role,sort_order,figures:pyq_figures(figure_key,storage_path,public_url))"
)
MAX_ANSWER_RETRIES = 6
PUBLISHABLE = frozenset({"auto_ok", "human_ok"})


def v2_json(model: str, messages: list, env: dict, limiter: p.RateLimiter, max_tokens: int) -> dict:
    raw = p.call_sarvam_v2(
        model,
        messages,
        env["SARVAM_API_KEY"],
        limiter,
        max_tokens=max_tokens,
        json_object=True,
        timeout=240.0,
    )
    return p.parse_json_content(raw)


def exam_year_of(row: dict) -> int | None:
    date = str(row.get("exam_date") or "")
    if len(date) >= 4 and date[:4].isdigit():
        return int(date[:4])
    return None


def normalize_row(row: dict) -> dict:
    opts = sorted(row.get("question_options") or [], key=lambda o: int(o.get("option_index") or 0))
    return {
        "id": row["id"],
        "q_no": int(row["q_no"]),
        "format": row.get("format") or "mcq",
        "body": row.get("body") or "",
        "options": [str(o.get("body") or "").strip() for o in opts],
        "correct_option": row.get("correct_option"),
        "numerical_answer": row.get("numerical_answer"),
        "exam_year": exam_year_of(row),
        "exam_date": row.get("exam_date"),
        "review_status": row.get("review_status"),
        "solution_md": row.get("solution_md"),
        "figure_links": row.get("figure_links") or [],
    }


def fetch_rows(sb, chapter_id: int) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        batch = (
            sb.table("pyq_questions")
            .select(SELECT)
            .eq("chapter_id", chapter_id)
            .in_("review_status", list(PUBLISHABLE))
            .range(start, start + 999)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < 1000:
            break
        start += 1000
    return [normalize_row(r) for r in rows]


def figure_png_path(row: dict) -> Path | None:
    for link in row.get("figure_links") or []:
        fig = (link or {}).get("figures") or {}
        key = str(fig.get("figure_key") or "").strip()
        if not key:
            continue
        local = p.OUT / "figures" / f"{key}.png"
        if local.is_file():
            return local
        url = str(fig.get("public_url") or "").strip()
        if not url:
            continue
        dest = p.OUT / "solution-figures" / f"{key}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file():
            return dest
        r = httpx.get(url, follow_redirects=True, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest
    return None


def describe_figure(png: Path, env: dict, limiter: p.RateLimiter) -> str:
    assert_model_may_see_image(VISION_DESCRIBE_MODEL)
    messages = [
        {"role": "system", "content": VISION_FIGURE_SYSTEM},
        *p.page_image_message(png, "Describe this exam figure as markdown."),
    ]
    data = v2_json(VISION_DESCRIBE_MODEL, messages, env, limiter, max_tokens=2048)
    return str(data.get("figure_md") or "").strip()


def ask_glm(packet: str, env: dict, limiter: p.RateLimiter, retry_note: str = "") -> dict:
    assert_solution_model(SOLUTION_MODEL)
    user = packet if not retry_note else f"{packet}\n\n{retry_note}"
    messages = [
        {"role": "system", "content": SOLUTION_SYSTEM},
        {"role": "user", "content": user},
    ]
    return v2_json(SOLUTION_MODEL, messages, env, limiter, max_tokens=16384)


def solve_one(row: dict, env: dict, limiter: p.RateLimiter, dry_run: bool) -> dict:
    key_type, key_value = official_key(row)
    figure_md = ""
    png = figure_png_path(row)
    if png is not None and not dry_run:
        try:
            figure_md = describe_figure(png, env, limiter)
        except Exception as exc:
            return {"id": row["id"], "q_no": row["q_no"], "ok": False, "error": f"vision: {exc}"}
    elif png is not None:
        figure_md = f"(figure file {png.name})"
    packet = combine_question_md(row, figure_md)
    if dry_run:
        return {"id": row["id"], "q_no": row["q_no"], "ok": True, "dry_run": True, "packet": packet}

    last_err = ""
    for attempt in range(1, MAX_ANSWER_RETRIES + 1):
        note = ""
        if last_err:
            note = (
                f"Previous attempt failed ({last_err}). "
                f"Return the step JSON (title, problem_tex, 4–8 steps, boxed displays, answer_tex). "
                f"Last step must be Official key {key_value}."
            )
            if "Unterminated" in last_err or "delimiter" in last_err:
                note += (
                    " Previous JSON was truncated. Use exactly 4 short steps, "
                    "one boxed display per step, no semicolon lists, no long evaluation dumps."
                )
        try:
            data = ask_glm(packet, env, limiter, note)
        except Exception as exc:
            last_err = str(exc)
            continue
        worked = normalize_worked_payload(data)
        answer = str((worked or data).get("answer") or "").strip()
        solution_md = dump_worked_payload(worked) if worked else ""
        if should_write_solution(
            answer=answer, key_type=key_type, key_value=key_value, solution_md=solution_md
        ):
            return {
                "id": row["id"],
                "q_no": row["q_no"],
                "ok": True,
                "answer": answer,
                "solution_md": solution_md,
                "attempts": attempt,
            }
        if not solution_md_complete(solution_md):
            last_err = f"bad phase JSON {str(data)[:80]!r}"
        else:
            last_err = f"got {answer!r}"
    return {"id": row["id"], "q_no": row["q_no"], "ok": False, "error": last_err or "no solution"}


def write_solution(sb, question_id: str, solution_md: str) -> None:
    last_exc: Exception | None = None
    for attempt in range(1, 6):
        try:
            sb.table("pyq_questions").update({"solution_md": solution_md}).eq("id", question_id).execute()
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(min(8, 2 ** attempt))
    raise last_exc if last_exc is not None else RuntimeError("write_solution failed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=("math", "physics"), required=True)
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--year", type=int)
    ap.add_argument("--whole-chapter", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--q-no", type=int, action="append", dest="q_nos")
    args = ap.parse_args()
    if args.year is None and not args.whole_chapter:
        ap.error("pass --year YYYY or --whole-chapter")

    sys.stdout.reconfigure(encoding="utf-8")
    spec = p.configure_book(args.book)
    env = p.load_env()
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, args.chapter, spec["subject_name"])
    loaded = fetch_rows(sb, chapter_id)
    jobs = jobs_for_scope(loaded, year=args.year, whole_chapter=args.whole_chapter)
    if args.q_nos:
        wanted = set(args.q_nos)
        jobs = [j for j in jobs if j["q_no"] in wanted]
    if not args.overwrite:
        jobs = [j for j in jobs if not str(j.get("solution_md") or "").strip()]
    if args.limit:
        jobs = jobs[: args.limit]
    if not jobs:
        print("no questions in scope", flush=True)
        return 0

    limiter = p.RateLimiter(18)
    dest_dir = p.OUT / "agents" / f"chapter_{args.chapter}" / "solutions"
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"{len(jobs)} questions in parallel | solver={SOLUTION_MODEL} | vision={VISION_DESCRIBE_MODEL}",
        flush=True,
    )
    results = []
    workers = max(1, len(jobs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(solve_one, job, env, limiter, args.dry_run): job for job in jobs}
        for fut in as_completed(futs):
            result = fut.result()
            results.append(result)
            tag = "OK" if result.get("ok") else "HOLD"
            print(f"[{tag}] Q{result['q_no']} {result.get('error') or ''}", flush=True)
            (dest_dir / f"q{result['q_no']}.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if result.get("ok") and result.get("solution_md") and not args.dry_run:
                try:
                    write_solution(sb, result["id"], result["solution_md"])
                except Exception as exc:
                    print(f"[HOLD] Q{result['q_no']} db-write: {exc}", flush=True)
                    result["ok"] = False
                    result["error"] = f"db-write: {exc}"

    holds = [r for r in results if not r.get("ok")]
    print(f"wrote {len(results) - len(holds)}/{len(results)}", flush=True)
    if holds:
        print("holds: " + ",".join(str(h["q_no"]) for h in holds), flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
