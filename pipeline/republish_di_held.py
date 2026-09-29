#!/usr/bin/env python3
"""Republish held Definite Integration rows using gemma4 vision.

Does not delete 2026 paper rows. Scoring still uses the PDF answer key.

    python republish_di_held.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import TIEBREAK_MODEL, VISION_MODEL
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from format_ocr_math import format_ocr_math
from ingest_di_yearbooks import (
    BOOKLETS,
    OUT,
    SUBJECT,
    CHAPTER_NO,
    clean_entry,
    dump,
    refine_type,
)
from ingest_math_2026_jan_definite import strip_branding
from run_chapter_agents import OBSERVER_SYSTEM, v2_json

SKIP_BOOKLETS = {"2026-jan"}


def load_skeleton() -> list[dict]:
    path = OUT / "all_skeleton.json"
    return json.loads(path.read_text(encoding="utf-8"))


def pick_vision(env: dict, limiter: p.RateLimiter, messages: list) -> tuple[str, dict]:
    try:
        return TIEBREAK_MODEL, v2_json(TIEBREAK_MODEL, messages, env, limiter)
    except Exception as flash_exc:
        print(f"    flash unavailable ({type(flash_exc).__name__}), using gemma4", flush=True)
        return VISION_MODEL, v2_json(VISION_MODEL, messages, env, limiter)


def transcribe_page(book_id: str, page_no: int, slice_: list, env: dict,
                    limiter: p.RateLimiter) -> dict:
    cache = OUT / book_id / "gemma4" / f"page_{page_no:03d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    png = OUT / book_id / "pages" / f"page_{page_no:03d}.png"
    if not png.exists():
        raise FileNotFoundError(png)
    allowed = [{"q_no": s["q_no"], "answer_type": s.get("answer_type")} for s in slice_]
    text = (
        "Transcribe every Definite Integration question on this printed page. "
        "Ignore solutions, other chapters, and branding. "
        "KaTeX with $...$. Do not solve.\n"
        + json.dumps(allowed, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": OBSERVER_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    model, data = pick_vision(env, limiter, messages)
    data["_model"] = model
    dump(cache, data)
    return data


def fetch_rows(sb, chapter_id: int) -> dict[tuple[str, int], dict]:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,review_status,format,source_bbox")
        .eq("chapter_id", chapter_id)
        .execute()
        .data
        or []
    )
    out = {}
    for row in rows:
        bbox = row.get("source_bbox") or {}
        booklet = bbox.get("booklet")
        pdf_q = bbox.get("pdf_q")
        if booklet is None or pdf_q is None:
            continue
        out[(booklet, int(pdf_q))] = row
    return out


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = [r for r in load_skeleton() if r.get("booklet") not in SKIP_BOOKLETS]
    by_page: dict[tuple[str, int], list] = defaultdict(list)
    for rec in skeleton:
        by_page[(rec["booklet"], rec["page"])].append(rec)

    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)

    holds = []
    live = 0
    for (book_id, page_no), slice_ in sorted(by_page.items()):
        print(f"vision {book_id} p{page_no} ({len(slice_)} q)", flush=True)
        try:
            data = transcribe_page(book_id, page_no, slice_, env, limiter)
        except Exception as exc:
            dump(OUT / book_id / "gemma4" / f"page_{page_no:03d}.error.json",
                 {"error": f"{type(exc).__name__}: {exc}"})
            print(f"  fail {type(exc).__name__}: {exc}", flush=True)
            for rec in slice_:
                holds.append({"booklet": book_id, "pdf_q": rec["q_no"], "reason": "vision"})
            continue
        by_q = {int(q["q_no"]): q for q in (data.get("questions") or []) if "q_no" in q}
        for rec in slice_:
            db = db_rows.get((book_id, rec["q_no"]))
            if db is None:
                holds.append({"booklet": book_id, "pdf_q": rec["q_no"], "reason": "missing_row"})
                continue
            raw = by_q.get(rec["q_no"]) or {}
            entry = clean_entry({
                "body": raw.get("body") or "",
                "options": raw.get("options"),
                "page": page_no,
            }, rec)
            rec = refine_type(dict(rec), entry)
            entry = clean_entry(entry, rec)
            shape_ok = shape_ok_for(rec, entry)
            audit_ok = not flags_for(entry.get("body") or "", is_option=False)
            if entry.get("options"):
                audit_ok = audit_ok and all(
                    not flags_for(o or "", is_option=True) for o in entry["options"]
                )
            fields = [entry.get("body") or ""] + (entry.get("options") or [])
            katex_ok = all(katex_render_ok(t) for t in fields if t is not None)
            solver_dump = is_solver_dump(entry.get("body") or "")
            key = rec.get("answer_value") or rec.get("raw_key")
            ok = shape_ok and audit_ok and katex_ok and not solver_dump and key not in (None, "")
            status = "human_ok" if ok else "unreviewed"
            if ok:
                live += 1
            else:
                holds.append({
                    "booklet": book_id, "pdf_q": rec["q_no"],
                    "shape_ok": shape_ok, "audit_ok": audit_ok, "katex_ok": katex_ok,
                    "key": key, "preview": (entry.get("body") or "")[:100],
                })
            sb.table("pyq_questions").update({"format": rec["answer_type"]}).eq("id", db["id"]).execute()
            upsert_question(
                sb, db["id"], entry, status,
                1.0 if ok else 0.5,
                rec,
                answer=str(key) if ok else None,
            )

    dump(OUT / "held_republish.json", holds)
    print(f"published {live}  holds {len(holds)}", flush=True)
    for h in holds[:30]:
        print(f"  hold {h.get('booklet')} Q{h.get('pdf_q')} {h.get('reason') or ''} "
              f"shape={h.get('shape_ok')} katex={h.get('katex_ok')}", flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    sys.exit(main())
