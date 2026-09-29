#!/usr/bin/env python3
"""Retry the few DI pages whose gemma4 JSON truncated."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import VISION_MODEL, PRIMARY_SOLVER
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from ingest_di_yearbooks import OUT, SUBJECT, CHAPTER_NO, clean_entry, dump, refine_type
from republish_di_held import fetch_rows, load_skeleton
from run_chapter_agents import OBSERVER_SYSTEM, v2_json

PAGES = [
    ("2020-sep", 4),
    ("2022-jul", 4),
    ("2024-jan", 2),
    ("2024-jan", 5),
    ("2025-jan", 39),
]


def transcribe(book_id: str, page_no: int, slice_: list, env: dict, limiter: p.RateLimiter) -> dict:
    cache = OUT / book_id / "gemma4" / f"page_{page_no:03d}.retry.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    png = OUT / book_id / "pages" / f"page_{page_no:03d}.png"
    allowed = [{"q_no": s["q_no"], "answer_type": s.get("answer_type")} for s in slice_]
    text = (
        "Transcribe the listed Definite Integration questions only. "
        "Short JSON. KaTeX $...$. Do not solve.\n"
        + json.dumps(allowed, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": OBSERVER_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    try:
        data = v2_json(VISION_MODEL, messages, env, limiter)
    except json.JSONDecodeError as exc:
        raw = str(exc)
        repair = [
            {"role": "system", "content": "Fix this truncated JSON so it is valid. Return JSON only."},
            {"role": "user", "content": raw[:8000]},
        ]
        data = v2_json(PRIMARY_SOLVER, repair, env, limiter)
    dump(cache, data)
    return data


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = load_skeleton()
    by_page = defaultdict(list)
    for rec in skeleton:
        by_page[(rec["booklet"], rec["page"])].append(rec)
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)
    live = 0
    holds = []
    for book_id, page_no in PAGES:
        slice_ = by_page[(book_id, page_no)]
        print(f"retry {book_id} p{page_no} ({len(slice_)} q)", flush=True)
        try:
            data = transcribe(book_id, page_no, slice_, env, limiter)
        except Exception as exc:
            print(f"  fail {type(exc).__name__}: {exc}", flush=True)
            continue
        by_q = {int(q["q_no"]): q for q in (data.get("questions") or []) if "q_no" in q}
        for rec in slice_:
            db = db_rows.get((book_id, rec["q_no"]))
            if db is None:
                continue
            raw = by_q.get(rec["q_no"]) or {}
            entry = clean_entry({"body": raw.get("body") or "", "options": raw.get("options"), "page": page_no}, rec)
            rec = refine_type(dict(rec), entry)
            entry = clean_entry(entry, rec)
            shape_ok = shape_ok_for(rec, entry)
            audit_ok = not flags_for(entry.get("body") or "", is_option=False)
            if entry.get("options"):
                audit_ok = audit_ok and all(not flags_for(o or "", is_option=True) for o in entry["options"])
            fields = [entry.get("body") or ""] + (entry.get("options") or [])
            katex_ok = all(katex_render_ok(t) for t in fields if t is not None)
            key = rec.get("answer_value") or rec.get("raw_key")
            ok = shape_ok and audit_ok and katex_ok and not is_solver_dump(entry.get("body") or "") and key not in (None, "")
            status = "human_ok" if ok else "unreviewed"
            if ok:
                live += 1
            else:
                holds.append({"booklet": book_id, "pdf_q": rec["q_no"], "shape_ok": shape_ok, "katex_ok": katex_ok, "key": key})
            sb.table("pyq_questions").update({"format": rec["answer_type"]}).eq("id", db["id"]).execute()
            upsert_question(sb, db["id"], entry, status, 1.0 if ok else 0.5, rec, answer=str(key) if ok else None)
    print(f"retry published {live} holds {holds}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
