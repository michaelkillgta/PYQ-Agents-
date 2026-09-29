#!/usr/bin/env python3
"""glm5.3 Tips / Formula's for every live PYQ that already has a solution.

No year or chapter lock. Skip empty solution_md. Skip existing tips unless --overwrite.

    python generate_pyq_coach.py
    python generate_pyq_coach.py --chapters 18,19,26
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import generate_di_coach as di
import pyq_common as p
from agents.models import PRIMARY_SOLVER

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-pyq-coach")
CACHE = OUT / "glm"
SUBJECT = "Mathematics"

SYSTEM = """You write JEE Main coach notes for Class 11–12 Indian students (NTA, NCERT).
You are given the chapter name, the printed question, and the worked solution. Understand all three, then return JSON only:
{"tips":[{"title":"2 to 5 words","body":"one or two short sentences with $KaTeX$","callout":"optional boxed $KaTeX$ identity"}],"formulas":[{"name":"NCERT/JEE name","tex":"latex without dollar signs","note":"when to use, under 12 words"}]}
Rules:
- Tips are a start path: 3 to 5 moves, in the order a student should think, taken from THIS solution.
- Each tip is one move for THIS chapter (trig general solution, n in Z, range of theta, King, GIF, variable separable, area split, …). Not a paragraph dump.
- Optional callout: one identity for that move, never the last boxed number or the correct option.
- Never state the numerical value, the correct option letter/number, or the last boxed result.
- Formulas: 2 to 5 identities actually used in THIS solution. One identity per card. tex is display latex only.
- NCERT / JEE Main names that belong to THIS chapter. Do not force integral properties onto trigonometry or vice versa.
- No IMO, A-level, AP, IB, Fredholm, Lebesgue, Hilbert, Banach, or other university-course names.
- Write \\pi not \\rho. JSON strings double every TeX backslash: \\\\sin \\\\cos \\\\frac \\\\pi \\\\sqrt.
- Formula name: short NCERT/JEE title. Any radical or trig value is $KaTeX$ ($\\\\dfrac{\\\\sqrt{3}}{2}$, $\\\\cos\\\\theta$), never ascii sqrt3 or 1/sqrt2."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def math_chapters(sb) -> list[dict]:
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
    unit_ids = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    rows = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,name,catalog_slug")
        .in_("unit_id", unit_ids)
        .execute()
        .data
        or []
    )
    rows.sort(key=lambda r: int(r["chapter_no"]))
    return rows


def ask(row: dict, env: dict, limiter: p.RateLimiter) -> dict:
    qid = row["id"]
    cache = CACHE / f"{qid}.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = None
        parsed = di.validate(data) if isinstance(data, dict) else None
        if parsed:
            tips, formulas = parsed
            return {"id": qid, "q_no": row["q_no"], "tips": tips, "formulas": formulas}
    opts = di.format_options(row)
    chapter = str(row.get("chapter_name") or "Mathematics")
    user = (
        f"CHAPTER\n{chapter}\n\n"
        f"QUESTION\n{row.get('body') or ''}\n"
        + (f"\nOPTIONS\n{opts}\n" if opts else "")
        + f"\nWORKED SOLUTION\n{di.paper_solution(row.get('solution_md') or '')}"
    )
    raw = p.call_sarvam_v2(
        PRIMARY_SOLVER,
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        env["SARVAM_API_KEY"],
        limiter,
        max_tokens=4096,
        json_object=True,
    )
    data = p.parse_json_content(raw)
    dump(cache, data)
    parsed = di.validate(data)
    if not parsed:
        raise ValueError(f"bad coach json q_no={row.get('q_no')} chapter={chapter}")
    tips, formulas = parsed
    return {"id": qid, "q_no": row["q_no"], "tips": tips, "formulas": formulas}


def fetch_rows(sb, chapters: list[dict], years: tuple[int, ...] | None) -> list[dict]:
    want_years = set(years) if years else None
    out = []
    for ch in chapters:
        rows = (
            sb.table("pyq_questions")
            .select(
                "id,q_no,exam_date,format,body,solution_md,tips_md,"
                "question_options:pyq_question_options(option_index,body)"
            )
            .eq("chapter_id", ch["id"])
            .in_("review_status", ["auto_ok", "human_ok"])
            .execute()
            .data
            or []
        )
        for row in rows:
            year = int(str(row.get("exam_date") or "0")[:4] or 0)
            if want_years is not None and year not in want_years:
                continue
            sol = str(row.get("solution_md") or "").strip()
            if len(sol) < 20:
                continue
            row["options"] = row.get("question_options") or []
            row["chapter_name"] = ch["name"]
            row["chapter_no"] = ch["chapter_no"]
            row["catalog_slug"] = ch["catalog_slug"]
            out.append(row)
    out.sort(key=lambda r: (int(r["chapter_no"]), str(r.get("exam_date") or ""), int(r["q_no"])))
    return out


def run_batch(rows: list[dict], env: dict, limiter: p.RateLimiter) -> tuple[dict[str, dict], list[str]]:
    got: dict[str, dict] = {}
    fails: list[str] = []
    if not rows:
        return got, fails
    with ThreadPoolExecutor(max_workers=len(rows)) as pool:
        futs = {pool.submit(ask, row, env, limiter): row["id"] for row in rows}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                rec = fut.result()
                got[qid] = rec
                print(
                    f"  ok q_no={rec['q_no']} tips={len(rec['tips'])} formulas={len(rec['formulas'])}",
                    flush=True,
                )
            except Exception as exc:
                fails.append(f"{qid[:8]} {exc}")
                print(f"  fail {qid[:8]} {exc}", flush=True)
    return got, fails


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="", help="comma years; empty = every year")
    parser.add_argument("--chapters", default="", help="comma PDF chapter_no; empty = every math chapter")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--ids", default="", help="comma question uuids; empty = every row in scope")
    args = parser.parse_args()
    years = tuple(int(y.strip()) for y in args.years.split(",") if y.strip()) or None
    want_ch = {int(x.strip()) for x in args.chapters.split(",") if x.strip()}
    want_ids = {x.strip() for x in args.ids.split(",") if x.strip()}
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    chapters = math_chapters(sb)
    if want_ch:
        chapters = [c for c in chapters if int(c["chapter_no"]) in want_ch]
    rows = fetch_rows(sb, chapters, years)
    if want_ids:
        rows = [r for r in rows if r["id"] in want_ids]
    if not args.overwrite:
        rows = [r for r in rows if not str(r.get("tips_md") or "").strip()]
    if not rows:
        print("nothing to generate", flush=True)
        return 0
    limiter = p.RateLimiter()
    print(
        f"{len(rows)} glm5.3 coach jobs in parallel chapters={[c['name'] for c in chapters]} years={list(years) if years else 'all'}",
        flush=True,
    )
    got, fails = run_batch(rows, env, limiter)
    if fails:
        retry = [r for r in rows if r["id"] not in got]
        print(f"retry {len(retry)}", flush=True)
        more, fails2 = run_batch(retry, env, limiter)
        got.update(more)
        fails = fails2
    for rec in got.values():
        payload = {"tips": rec["tips"]}
        forms = {"formulas": rec["formulas"]}
        sb.table("pyq_questions").update({
            "tips_md": json.dumps(payload, ensure_ascii=False),
            "formulas_md": json.dumps(forms, ensure_ascii=False),
        }).eq("id", rec["id"]).execute()
    print(f"published {len(got)}", flush=True)
    if fails:
        print("fails", fails, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
