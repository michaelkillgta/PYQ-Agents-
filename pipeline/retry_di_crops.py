#!/usr/bin/env python3
"""Crop leftover held DI questions and republish 2020-sep Q5/Q10 without a second wrap."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.models import TIEBREAK_MODEL, VISION_MODEL
from finish_di_remaining import (
    SEP_KEYS,
    SEP_META,
    fetch_rows,
    pick_question,
    publish_row,
    spec_from_skeleton,
    transcribe_one,
)
from ingest_di_yearbooks import BOOKLETS, CHAPTER_NO, OUT, SUBJECT, dump
from repair_held_pyq import CROP_SYSTEM
from run_chapter_agents import v2_json

DPI = 200
CROPS = [
    ("2020-sep", 4, 1),
    ("2022-jun", 4, 1),
    ("2022-jul", 3, 1),
    ("2022-jul", 6, 2),
    ("2022-jul", 14, 5),
]


def book_pdf(book_id: str) -> Path:
    for book in BOOKLETS:
        if book["id"] == book_id:
            return book["pdf"]
    raise KeyError(book_id)


def crop_question(pdf: Path, page_no: int, q_no: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    page = doc[page_no - 1]
    needles = [f"Q{q_no} -", f"Q{q_no} JEE", f"Q{q_no}."]
    hits = []
    for needle in needles:
        hits.extend(page.search_for(needle))
    if not hits:
        hits = page.search_for(f"Q{q_no}")
    if not hits:
        doc.close()
        raise FileNotFoundError(f"no header Q{q_no} on {pdf.name} p{page_no}")
    start = min(hits, key=lambda r: (r.y0, r.x0))
    next_hits = []
    for later in range(q_no + 1, q_no + 8):
        for needle in (f"Q{later} -", f"Q{later} JEE", f"Q{later}."):
            next_hits.extend(page.search_for(needle))
        if not next_hits:
            next_hits.extend(page.search_for(f"Q{later}"))
        if next_hits:
            next_hits = [r for r in next_hits if r.y0 > start.y0 + 8]
        if next_hits:
            break
    y0 = max(0, start.y0 - 6)
    y1 = min(h.y0 for h in next_hits) - 4 if next_hits else page.rect.y1 - 36
    if y1 - y0 < 40:
        y1 = min(page.rect.y1 - 8, y0 + 220)
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip, alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def observe_crop(png: Path, spec: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = OUT / spec["booklet"] / "gemma4" / f"crop_q{spec['q_no']:02d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    text = (
        f"Transcribe ONLY Q{spec['q_no']} in this crop. "
        "If (1)(2)(3)(4) or (A)(B)(C)(D) are printed, return four options. "
        "KaTeX $...$. Do not solve."
    )
    messages = [{"role": "system", "content": CROP_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    try:
        data = v2_json(TIEBREAK_MODEL, messages, env, limiter)
        data["_model"] = TIEBREAK_MODEL
    except Exception as exc:
        print(f"    flash fail {type(exc).__name__}, gemma4", flush=True)
        data = v2_json(VISION_MODEL, messages, env, limiter)
        data["_model"] = VISION_MODEL
    dump(cache, data)
    return data


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = json.loads((OUT / "all_skeleton.json").read_text(encoding="utf-8"))
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)

    print("republish 2020-sep Q5 Q10 from cache", flush=True)
    for pdf_q in (5, 10):
        page, date, shift = SEP_META[pdf_q]
        raw = SEP_KEYS[pdf_q]
        spec = {
            "q_no": pdf_q, "page": page, "exam_date": date, "exam_shift": shift,
            "booklet": "2020-sep", "answer_type": "mcq",
            "answer_value": str("ABCD".index(raw) + 1), "raw_key": raw,
            "figure_keys": [],
        }
        data = transcribe_one("2020-sep", pdf_q, page, spec, env, limiter)
        q = pick_question(data, pdf_q)
        ok, reason = publish_row(sb, db_rows[("2020-sep", pdf_q)], spec, {
            "body": q.get("body") or "", "options": q.get("options"), "page": page,
        }, env, limiter)
        print(f"  2020-sep Q{pdf_q} {reason}", flush=True)

    holds = []
    for book_id, pdf_q, page in CROPS:
        spec = spec_from_skeleton(skeleton, book_id, pdf_q) if book_id != "2020-sep" else {
            "q_no": pdf_q,
            "page": page,
            "exam_date": SEP_META[pdf_q][1],
            "exam_shift": SEP_META[pdf_q][2],
            "booklet": "2020-sep",
            "answer_type": "mcq",
            "answer_value": str("ABCD".index(SEP_KEYS[pdf_q]) + 1),
            "raw_key": SEP_KEYS[pdf_q],
            "figure_keys": [],
        }
        if book_id != "2020-sep":
            spec = spec_from_skeleton(skeleton, book_id, pdf_q)
        db = db_rows[(book_id, pdf_q)]
        png = OUT / book_id / "crops" / f"q{pdf_q:02d}.png"
        print(f"crop {book_id} Q{pdf_q}", flush=True)
        try:
            crop_question(book_pdf(book_id), page, pdf_q, png)
        except Exception as exc:
            print(f"  crop fail {exc}", flush=True)
            holds.append((book_id, pdf_q, f"crop:{exc}"))
            continue
        try:
            data = observe_crop(png, spec, env, limiter)
        except Exception as exc:
            print(f"  vision fail {exc}", flush=True)
            holds.append((book_id, pdf_q, f"vision:{exc}"))
            continue
        raw = pick_question(data, pdf_q) or data
        body = (raw.get("body") or "").strip()
        if not body:
            holds.append((book_id, pdf_q, "empty"))
            print("  empty", flush=True)
            continue
        ok, reason = publish_row(sb, db, spec, {
            "body": body, "options": raw.get("options"), "page": page,
        }, env, limiter)
        print(f"  {reason}", flush=True)
        if not ok:
            holds.append((book_id, pdf_q, reason))

    dump(OUT / "retry_crops.json", {"holds": holds})
    print(f"still_held {len(holds)}", flush=True)
    for item in holds:
        print("  HOLD", item, flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    sys.exit(main())
