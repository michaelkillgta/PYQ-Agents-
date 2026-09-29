#!/usr/bin/env python3
"""Retry leftover empty / junk GLM answers on math chapter 5. No OCR."""
from __future__ import annotations

import json
import time

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import SOLVER_A, SOLVER_B
from agents.promotion import final_publish_status
from agents.publish import shape_ok_for, upsert_question
from agents.report import build_report
from agents.solvers import solve_match
from audit_paper_text import flags_for
from run_chapter_agents import (
    answer_for,
    chapter_dir,
    dump,
    solver_answer,
    spec_map,
    write_hold_json,
)

CHAPTER_NO = 5
JUNK = {"", "...", "?", "null", "none"}


def main() -> int:
    book_spec = p.configure_book("math")
    env = p.load_env()
    limiter = p.RateLimiter(20)
    out_dir = chapter_dir(CHAPTER_NO)
    specs = spec_map(p.load_skeleton(), CHAPTER_NO)
    parsed = {int(k): v for k, v in json.loads((out_dir / "parsed.json").read_text(encoding="utf-8")).items()}
    solvers = json.loads((out_dir / "solvers.json").read_text(encoding="utf-8"))
    key_book = p.load_answer_key()
    sb = p.supabase_client()
    ch_id = p.resolve_chapter_id(sb, CHAPTER_NO, book_spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    retry_q = []
    for q_no in sorted(specs):
        row = solvers.get(str(q_no)) or {}
        glm = str(row.get("glm") or "").strip().lower()
        ds = str(row.get("deepseek") or "").strip().lower()
        if glm in JUNK or ds in JUNK:
            retry_q.append(q_no)
    print(f"retry {len(retry_q)} q: {retry_q}", flush=True)

    for q_no in retry_q:
        spec = specs[q_no]
        entry = parsed[q_no]
        key_row = answer_for(key_book, CHAPTER_NO, q_no)
        glm_ans = ds_ans = None
        last_err = None
        for attempt in range(6):
            try:
                glm_ans = solver_answer(SOLVER_A, entry, spec, {}, env, limiter)
                ds_ans = solver_answer(SOLVER_B, entry, spec, {}, env, limiter)
                if str(glm_ans).strip().lower() not in JUNK and str(ds_ans).strip().lower() not in JUNK:
                    last_err = None
                    break
                last_err = ValueError("empty model content")
            except Exception as exc:
                last_err = exc
                time.sleep(min(2 ** attempt, 20))
        match = False
        if key_row and glm_ans is not None and ds_ans is not None:
            match = solve_match(str(glm_ans), str(ds_ans), key_row["type"], key_row["value"])
        solvers[str(q_no)] = {
            "glm": glm_ans,
            "deepseek": ds_ans,
            "key": None if key_row is None else key_row["value"],
            "match": match,
            "retry_error": None if last_err is None else f"{type(last_err).__name__}: {last_err}",
        }
        dump(out_dir / "solvers.json", solvers)
        print(f"  q{q_no} glm={glm_ans!r} ds={ds_ans!r} match={match}", flush=True)

        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        katex_ok = all(katex_render_ok(t) for t in fields)
        audit_ok = not flags_for(entry.get("body") or "", is_option=False)
        for opt in entry.get("options") or []:
            audit_ok = audit_ok and not [f for f in flags_for(opt or "", is_option=True) if not str(f).startswith("empty")]
        dump_ok = not is_solver_dump(entry.get("body") or "")
        shape_ok = shape_ok_for(spec, entry)
        gates = {
            "skeleton": True,
            "shape_ok": shape_ok,
            "coverage_ok": True,
            "vision_ok": True,
            "figures_ok": True,
            "audit_ok": audit_ok and dump_ok,
            "katex_ok": katex_ok,
            "solve_match": match,
            "confidence": 1.0,
        }
        status = final_publish_status(gates, entry.get("body") or "")
        if status != "auto_ok":
            status = "unreviewed"
        answer = None if key_row is None else str(key_row["value"])
        upsert_question(
            sb, q_ids[q_no], entry, status,
            1.0 if status == "auto_ok" else 0.5,
            spec, answer=answer if status == "auto_ok" else None,
        )

    holds = json.loads((out_dir / "hold.json").read_text(encoding="utf-8"))["holds"]
    keep = []
    touched = set(retry_q)
    for h in holds:
        if h.get("q_no") in touched and h.get("reason") in ("empty_model", "solver_parse", "solver_mismatch"):
            continue
        keep.append(h)
    for q_no in retry_q:
        row = solvers[str(q_no)]
        if row.get("match"):
            continue
        glm, ds = row.get("glm"), row.get("deepseek")
        if glm is None or ds is None or str(glm).strip().lower() in JUNK:
            keep.append({"q_no": q_no, "reason": "empty_model", "detail": row.get("retry_error") or "empty model content", "decision": None})
        else:
            keep.append({
                "q_no": q_no,
                "reason": "solver_mismatch",
                "pdf_key": row.get("key"),
                "glm": glm,
                "deepseek": ds,
                "stem_preview": (parsed[q_no].get("body") or "")[:160],
                "decision": None,
            })
    write_hold_json(out_dir, CHAPTER_NO, keep)
    (out_dir / "REPORT.md").write_text(build_report(CHAPTER_NO, keep), encoding="utf-8")
    rows = sb.table("pyq_questions").select("q_no,review_status").eq("chapter_id", ch_id).execute().data
    by = {}
    for r in rows:
        by[r["review_status"]] = by.get(r["review_status"], 0) + 1
    pub = by.get("auto_ok", 0) + by.get("human_ok", 0)
    held = sum(v for k, v in by.items() if k not in ("auto_ok", "human_ok"))
    print("DB status", by)
    print(f"publishable={pub} held={held} unique_holds={len({h.get('q_no') for h in keep if h.get('q_no')})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
