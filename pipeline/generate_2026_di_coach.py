#!/usr/bin/env python3
"""glm5.3 reads each 2026 DI question + solution, then writes Tips / Formula's JSON.

    python generate_2026_di_coach.py
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import PRIMARY_SOLVER
from ingest_math_2026_jan_di_solutions import EXPECT, fetch_2026_jan_rows

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-2026-jan-di-coach")
CACHE = OUT / "glm"
LEAK = re.compile(
    r"\b(option\s*[1-4]|correct option|the answer is|final answer|equals\s+\d+)\b",
    re.I,
)

SYSTEM = """You write JEE Main coach notes for Class 11–12 Indian students (NTA, NCERT).
You are given the printed question and the worked solution. Understand both, then return JSON only:
{"tips":[{"title":"2 to 5 words","body":"one or two short sentences with $KaTeX$"}],"formulas":[{"name":"NCERT/JEE name","tex":"latex without dollar signs","note":"when to use, under 12 words"}]}
Rules:
- Tips are a start path: 3 to 5 moves, in the order a student should think, taken from THIS solution.
- Each tip is one move (symmetry, split, substitute, GIF slab, x to a+b-x). Not a paragraph dump.
- Never state the numerical value, the correct option, or the last boxed result.
- Formulas: 2 to 5 identities actually used in THIS solution. One identity per card. tex is display latex only.
- NCERT Class 12 Integrals / JEE Main wording. No IMO, A-level, AP, or international contest language.
- JSON strings double every TeX backslash: \\\\int \\\\frac \\\\pi."""


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
    return t


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
        body = str(rec.get("body") or "").strip()
        if not title or not body or LEAK.search(body) or LEAK.search(title):
            continue
        if len(title) > 42:
            title = " ".join(title.split()[:5])
        tips.append({"title": title, "body": body})
    formulas = []
    for rec in forms_in:
        if not isinstance(rec, dict):
            continue
        name = re.sub(r"\s+", " ", str(rec.get("name") or "")).strip()
        tex = clean_tex(str(rec.get("tex") or ""))
        note = str(rec.get("note") or "").strip()
        if not name or not tex or LEAK.search(note):
            continue
        formulas.append({"name": name[:48], "tex": tex, "note": note})
    if len(tips) < 3 or len(formulas) < 2:
        return None
    return tips[:5], formulas[:5]


def ask(row: dict, env: dict, limiter: p.RateLimiter) -> dict:
    qid = row["id"]
    cache = CACHE / f"{qid}.json"
    if cache.is_file():
        data = json.loads(cache.read_text(encoding="utf-8"))
        parsed = validate(data)
        if parsed:
            tips, formulas = parsed
            return {"id": qid, "q_no": row["q_no"], "tips": tips, "formulas": formulas}
    user = (
        f"QUESTION\n{row.get('body') or ''}\n\n"
        f"WORKED SOLUTION\n{paper_solution(row.get('solution_md') or '')}"
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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    cid = p.resolve_chapter_id(sb, 17, "Mathematics")
    rows = list(fetch_2026_jan_rows(sb, cid).values())
    if len(rows) != EXPECT:
        raise SystemExit(f"expected {EXPECT} rows, got {len(rows)}")
    limiter = p.RateLimiter()
    print(f"{len(rows)} glm5.3 coach jobs in parallel", flush=True)
    got: dict[str, dict] = {}
    fails = []
    with ThreadPoolExecutor(max_workers=len(rows)) as pool:
        futs = {pool.submit(ask, row, env, limiter): row["id"] for row in rows}
        for fut in as_completed(futs):
            qid = futs[fut]
            try:
                rec = fut.result()
                got[qid] = rec
                print(f"  ok q_no={rec['q_no']} tips={len(rec['tips'])} formulas={len(rec['formulas'])}", flush=True)
            except Exception as exc:
                fails.append(f"{qid[:8]} {exc}")
                print(f"  fail {qid[:8]} {exc}", flush=True)
    if fails:
        print("fails", fails, flush=True)
        return 1
    for rec in got.values():
        sb.table("pyq_questions").update({
            "tips_md": json.dumps({"tips": rec["tips"]}, ensure_ascii=False),
            "formulas_md": json.dumps({"formulas": rec["formulas"]}, ensure_ascii=False),
        }).eq("id", rec["id"]).execute()
    print(f"published {len(got)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
