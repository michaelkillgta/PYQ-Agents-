#!/usr/bin/env python3
"""Repair quadratic-equation held rows from cached OCR + parallel GLM. No Document AI."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import SOLVER_A, SOLVER_B, TIEBREAK_MODEL
from agents.publish import shape_ok_for, upsert_question
from agents.solvers import parse_mcq_choice, solve_match
from bakeoff import page_slice
from parse_ocr_page import parse_digitise_to_questions

HELD = {
    1, 2, 5, 8, 10, 20, 21, 22, 24, 62, 64, 68, 72, 74, 75, 77, 78, 79, 84,
    92, 94, 95, 99, 101, 102, 104, 106, 107, 111, 115, 118, 121, 124, 128, 130,
}
PAGES = (7, 8, 10, 11, 12, 13)
CHAPTER = 2
WRAP_SYS = (
    "Transcribe printed JEE Main questions. JSON only: "
    '{"questions":[{"q_no":int,"body":str,"options":[str,str,str,str]|null}]}. '
    "MCQ: exactly four options. Numerical: options null. Wrap math in $...$. "
    "Paper text only. No solving, no Case 1, no boxed."
)
SOLVE_SYS = (
    'Solve. JSON {"answer":"..."}. MCQ answer is 1, 2, 3, or 4. '
    "Numerical is the number, no units. No explanation."
)


def load_ocr(page: int) -> dict:
    path = p.OUT / "ocr" / f"page_{page:03d}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def fields_ok(spec: dict, entry: dict) -> bool:
    body = (entry.get("body") or "").strip()
    if not body or body.startswith("(OCR missed") or is_solver_dump(body):
        return False
    texts = [body, *(entry.get("options") or [])]
    if not all(katex_render_ok(t) for t in texts):
        return False
    return shape_ok_for(spec, entry)


def wrap_page(page: int, slice_: list, api_key: str, limiter: p.RateLimiter) -> dict[int, dict]:
    wanted = [s for s in slice_ if s["q_no"] in HELD]
    if not wanted:
        return {}
    png = p.OUT / "pages" / f"page_{page:03d}.png"
    prompt = (
        f"Page {page}. Transcribe only q_no { [s['q_no'] for s in wanted] }. "
        "Keep printed option order."
    )
    raw = p.call_sarvam_v2(
        TIEBREAK_MODEL,
        [{"role": "system", "content": WRAP_SYS}, *p.page_image_message(png, prompt)],
        api_key,
        limiter,
        max_tokens=4096,
    )
    payload = p.parse_json_content(raw)
    out = {}
    for q in payload.get("questions") or []:
        q_no = int(q.get("q_no") or 0)
        if q_no not in HELD:
            continue
        spec = next(s for s in wanted if s["q_no"] == q_no)
        opts = q.get("options")
        if spec["answer_type"] != "mcq":
            opts = None
        out[q_no] = {"q_no": q_no, "body": q.get("body") or "", "options": opts}
    return out


def solve_one(q_no: int, spec: dict, entry: dict, api_key: str, limiter: p.RateLimiter, model: str) -> str:
    opts = entry.get("options")
    blob = (entry.get("body") or "") + "\n"
    if opts:
        blob += "\n".join(f"({i}) {o}" for i, o in enumerate(opts, 1))
    kind = spec["answer_type"]
    raw = p.call_sarvam_v2(
        model,
        [
            {"role": "system", "content": SOLVE_SYS},
            {"role": "user", "content": f"Type {kind}.\n{blob}"},
        ],
        api_key,
        limiter,
        max_tokens=256,
    )
    ans = str(p.parse_json_content(raw).get("answer") or "").strip()
    return ans


def main() -> int:
    p.configure_book("math")
    env = p.load_env()
    api_key = env["SARVAM_API_KEY"]
    limiter = p.RateLimiter(120)
    skeleton = p.load_skeleton()
    key_book = p.load_answer_key()["2"]["answers"]
    specs = {}
    for r in skeleton:
        if r["chapter_no"] != CHAPTER or r["q_no"] not in HELD:
            continue
        ans = key_book[str(r["q_no"])]
        specs[r["q_no"]] = {
            **r,
            "answer_type": ans["type"],
            "answer_value": ans["value"],
        }

    parsed: dict[int, dict] = {}
    for page in PAGES:
        slice_ = [s for s in page_slice(skeleton, page) if s["q_no"] in HELD]
        if not slice_:
            continue
        for q in parse_digitise_to_questions(load_ocr(page), slice_):
            parsed[int(q["q_no"])] = q

    need_wrap = [q_no for q_no, spec in specs.items() if not fields_ok(spec, parsed.get(q_no) or {})]
    print("ocr_ok", len(specs) - len(need_wrap), "need_wrap", need_wrap, flush=True)

    if need_wrap:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = {}
            for page in PAGES:
                slice_ = [s for s in page_slice(skeleton, page) if s["q_no"] in need_wrap]
                if slice_:
                    futs[pool.submit(wrap_page, page, slice_, api_key, limiter)] = page
            for fut in as_completed(futs):
                page = futs[fut]
                try:
                    got = fut.result()
                except Exception as exc:
                    print("wrap_fail", page, type(exc).__name__, exc, flush=True)
                    continue
                parsed.update(got)
                print("wrapped_page", page, sorted(got), flush=True)

    sb = p.supabase_client()
    ch_id = (
        sb.table("pyq_chapters")
        .select("id")
        .eq("unit_id", 3)
        .eq("catalog_slug", "quadratic-equation")
        .execute()
        .data[0]["id"]
    )
    q_rows = (
        sb.table("pyq_questions").select("id,q_no").eq("chapter_id", ch_id).execute().data
    )
    q_ids = {int(r["q_no"]): r["id"] for r in q_rows}

    published, still = [], []
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no) or {}
        ok = fields_ok(spec, entry)
        status = "human_ok" if ok else "unreviewed"
        upsert_question(sb, q_ids[q_no], entry, status, 1.0 if ok else 0.5, spec, spec["answer_value"])
        (published if ok else still).append(q_no)
    print("published", published, flush=True)
    print("still_held", still, flush=True)

    report = []
    targets = [q_no for q_no in published + still if q_no in parsed]

    def one(q_no: int, model: str) -> tuple[int, str, str]:
        return q_no, model, solve_one(q_no, specs[q_no], parsed[q_no], api_key, limiter, model)

    glm: dict[int, str] = {}
    ds: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs = []
        for q_no in targets:
            futs.append(pool.submit(one, q_no, SOLVER_A))
            futs.append(pool.submit(one, q_no, SOLVER_B))
        for fut in as_completed(futs):
            try:
                q_no, model, ans = fut.result()
            except Exception as exc:
                print("solve_fail", exc, flush=True)
                continue
            (glm if model == SOLVER_A else ds)[q_no] = ans

    mismatches = []
    for q_no in targets:
        spec = specs[q_no]
        pdf = str(spec["answer_value"])
        g = glm.get(q_no, "")
        d = ds.get(q_no, "")
        match = False
        try:
            match = solve_match(g, d, spec["answer_type"], pdf)
        except Exception:
            match = False
        row = {
            "q_no": q_no,
            "pdf": pdf,
            "glm5.3": g,
            "deepseek": d,
            "agree_with_pdf": match,
            "status": "live" if q_no in published else "held",
        }
        report.append(row)
        if not match:
            mismatches.append(row)
        print(row, flush=True)

    out = p.OUT / "agents" / "chapter_2" / "held_repair.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"published": published, "held": still, "report": report}, indent=1), encoding="utf-8")
    print("MISMATCHES", mismatches, flush=True)
    print("DONE live", len(published), "held", len(still), "mismatches", len(mismatches), flush=True)
    return 0 if not still else 2


if __name__ == "__main__":
    sys.exit(main())
