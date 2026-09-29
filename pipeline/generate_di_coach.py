#!/usr/bin/env python3
"""glm5.3 writes Tips / Formula's for Definite Integration PYQs.

Default: 2023–2025 (2026 already published). Question + solution in, JSON out.

    python generate_di_coach.py
    python generate_di_coach.py --years 2023,2024,2025
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import PRIMARY_SOLVER

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-di-coach")
CACHE = OUT / "glm"
CHAPTER_NO = 17
SUBJECT = "Mathematics"
YEARS_DEFAULT = (2023, 2024, 2025)

LEAK = re.compile(
    r"\\boxed|\b(option\s*[1-4]|correct option|the answer is|final answer)\b",
    re.I,
)
BAN = re.compile(
    r"\b(Fredholm|Lebesgue|Hilbert|Banach|Weierstrass|IMO|A-level|AP Calculus)\b",
    re.I,
)

SYSTEM = """You write JEE Main coach notes for Class 11–12 Indian students (NTA, NCERT).
You are given the printed question and the worked solution. Understand both, then return JSON only:
{"tips":[{"title":"2 to 5 words","body":"one or two short sentences with $KaTeX$","callout":"optional boxed $KaTeX$ identity"}],"formulas":[{"name":"NCERT/JEE name","tex":"latex without dollar signs","note":"when to use, under 12 words"}]}
Rules:
- Tips are a start path: 3 to 5 moves, in the order a student should think, taken from THIS solution.
- Each tip is one move (symmetry, split, substitute, GIF slab, x to a+b-x). Not a paragraph dump.
- Optional callout: one identity for that move, never the last boxed number or the correct option.
- Never state the numerical value, the correct option letter/number, or the last boxed result.
- Formulas: 2 to 5 identities actually used in THIS solution. One identity per card. tex is display latex only.
- NCERT Class 12 Integrals / JEE Main wording. King property, GIF, odd/even, x to a+b-x are fine.
- No IMO, A-level, AP, IB, Fredholm, Lebesgue, Hilbert, Banach, or other university-course names.
- Write \\pi not \\rho. JSON strings double every TeX backslash: \\\\int \\\\frac \\\\pi \\\\sqrt.
- Formula name: short NCERT/JEE title. Any radical or trig value is $KaTeX$ ($\\\\dfrac{\\\\sqrt{3}}{2}$), never ascii sqrt3."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def paper_solution(md: str) -> str:
    text = re.sub(r"<!--\s*paper-ocr\s*-->", "", md or "", flags=re.I)
    text = re.sub(r"^##\s+.*$", "", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_tex(raw: str) -> str:
    t = str(raw or "").strip()
    if t.startswith("$$") and t.endswith("$$"):
        t = t[2:-2].strip()
    if t.startswith("$") and t.endswith("$"):
        t = t[1:-1].strip()
    return t.replace("\\rho", "\\pi")


def dirty(text: str) -> bool:
    return bool(LEAK.search(text) or BAN.search(text))


def validate(data: dict) -> tuple[list[dict], list[dict]] | None:
    tips_in = data.get("tips") if isinstance(data, dict) else None
    forms_in = data.get("formulas") if isinstance(data, dict) else None
    if not isinstance(tips_in, list) or not isinstance(forms_in, list):
        return None
    tips = []
    for rec in tips_in:
        if not isinstance(rec, dict):
            continue
        title = re.sub(r"\s+", " ", str(rec.get("title") or "")).strip()
        body = str(rec.get("body") or "").strip().replace("\\rho", "\\pi")
        callout = str(rec.get("callout") or "").strip().replace("\\rho", "\\pi")
        if not title or not body or dirty(title) or dirty(body) or dirty(callout):
            continue
        if len(title) > 42:
            title = " ".join(title.split()[:5])
        step = {"title": title, "body": body}
        if callout:
            step["callout"] = callout
        tips.append(step)
    formulas = []
    for rec in forms_in:
        if not isinstance(rec, dict):
            continue
        name = re.sub(r"\s+", " ", str(rec.get("name") or "")).strip()
        tex = clean_tex(str(rec.get("tex") or ""))
        note = str(rec.get("note") or "").strip()
        if not name or not tex or dirty(name) or dirty(note) or dirty(tex):
            continue
        formulas.append({"name": name[:48], "tex": tex, "note": note})
    if len(tips) < 3 or len(formulas) < 2:
        return None
    return tips[:5], formulas[:5]


def format_options(row: dict) -> str:
    opts = row.get("options") or []
    if not opts:
        return ""
    lines = []
    for item in sorted(opts, key=lambda o: int(o.get("option_index") or 0)):
        idx = item.get("option_index")
        body = str(item.get("body") or "").strip()
        if idx and body:
            lines.append(f"({idx}) {body}")
    return "\n".join(lines)


def ask(row: dict, env: dict, limiter: p.RateLimiter) -> dict:
    qid = row["id"]
    cache = CACHE / f"{qid}.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = None
        parsed = validate(data) if isinstance(data, dict) else None
        if parsed:
            tips, formulas = parsed
            return {"id": qid, "q_no": row["q_no"], "tips": tips, "formulas": formulas}
    opts = format_options(row)
    user = (
        f"QUESTION\n{row.get('body') or ''}\n"
        + (f"\nOPTIONS\n{opts}\n" if opts else "")
        + f"\nWORKED SOLUTION\n{paper_solution(row.get('solution_md') or '')}"
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
    parsed = validate(data)
    if not parsed:
        raise ValueError(f"bad coach json q_no={row.get('q_no')}")
    tips, formulas = parsed
    return {"id": qid, "q_no": row["q_no"], "tips": tips, "formulas": formulas}


def fetch_rows(sb, chapter_id: int, years: tuple[int, ...]) -> list[dict]:
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,format,body,solution_md,tips_md,"
            "question_options:pyq_question_options(option_index,body)"
        )
        .eq("chapter_id", chapter_id)
        .in_("review_status", ["auto_ok", "human_ok"])
        .execute()
        .data
        or []
    )
    want = set(years)
    out = []
    for row in rows:
        year = int(str(row.get("exam_date") or "0")[:4] or 0)
        if year not in want:
            continue
        sol = str(row.get("solution_md") or "").strip()
        if len(sol) < 20:
            continue
        row["options"] = row.get("question_options") or []
        out.append(row)
    out.sort(key=lambda r: (str(r.get("exam_date") or ""), int(r["q_no"])))
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
    parser.add_argument("--years", default="2023,2024,2025")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    years = tuple(int(y.strip()) for y in args.years.split(",") if y.strip())
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    cid = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    rows = fetch_rows(sb, cid, years)
    if not args.overwrite:
        rows = [r for r in rows if not str(r.get("tips_md") or "").strip()]
    if not rows:
        print("nothing to generate", flush=True)
        return 0
    limiter = p.RateLimiter()
    print(f"{len(rows)} glm5.3 coach jobs in parallel years={list(years)}", flush=True)
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
