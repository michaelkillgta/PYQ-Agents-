#!/usr/bin/env python3
"""Fill straddling DI questions from the top of the next page."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.models import TIEBREAK_MODEL, VISION_MODEL
from finish_di_remaining import fetch_rows, pick_question, publish_row
from ingest_di_yearbooks import BOOKLETS, CHAPTER_NO, OUT, SUBJECT, dump
from repair_held_pyq import CROP_SYSTEM
from run_chapter_agents import v2_json

DPI = 200

# booklet, pdf_q, continuation_page, key, kind
# kind: mcq letter or numerical string from the printed answer key
JOBS = [
    ("2020-sep", 4, 2, "A", "mcq", {
        "exam_date": "2020-01-08", "exam_shift": "evening", "page": 1,
        "body": r"Let $I = \int_{1}^{2} \frac{dx}{\sqrt{2x^{3}-9x^{2}+12x+4}}$ then",
        "options": [
            r"$\frac{1}{9} < I^{2} < \frac{1}{8}$",
            r"$\frac{1}{3} < I^{2} < \frac{1}{2}$",
            r"$\frac{1}{9} < I < \frac{1}{8}$",
            r"$\frac{1}{3} < I < \frac{1}{2}$",
        ],
    }),
    ("2022-jun", 4, 2, "A", "mcq", None),
    ("2022-jul", 3, 2, "B", "mcq", None),
    ("2022-jul", 6, 3, "C", "mcq", None),
    ("2022-jul", 14, 6, "A", "mcq", None),
]


def book_pdf(book_id: str) -> Path:
    for book in BOOKLETS:
        if book["id"] == book_id:
            return book["pdf"]
    raise KeyError(book_id)


def crop_page_top(pdf: Path, page_no: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    page = doc[page_no - 1]
    hits = []
    for n in range(1, 30):
        hits.extend(page.search_for(f"Q{n} -"))
        hits.extend(page.search_for(f"Q{n} JEE"))
    if not hits:
        doc.close()
        raise FileNotFoundError(f"no later header on {pdf.name} p{page_no}")
    first = min(hits, key=lambda r: r.y0)
    y0 = 42
    y1 = first.y0 - 2
    if y1 - y0 < 50:
        y1 = min(page.rect.y1 - 40, y0 + 260)
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1 * 0.72, y1)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip, alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def observe(png: Path, spec: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = OUT / spec["booklet"] / "gemma4" / f"top_q{spec['q_no']:02d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    text = (
        f"Transcribe the incomplete question at the TOP of this crop (it is Q{spec['q_no']}). "
        "Ignore later Q-headers. If four options are printed, return them. "
        "KaTeX $...$. Do not solve."
    )
    messages = [{"role": "system", "content": CROP_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    try:
        data = v2_json(TIEBREAK_MODEL, messages, env, limiter)
        data["_model"] = TIEBREAK_MODEL
    except Exception:
        data = v2_json(VISION_MODEL, messages, env, limiter)
        data["_model"] = VISION_MODEL
    dump(cache, data)
    return data


def spec_of(book_id: str, pdf_q: int, key: str, kind: str, extra: dict | None) -> dict:
    if kind == "mcq":
        value = str("ABCD".index(key) + 1)
        atype = "mcq"
    else:
        value = key
        atype = "numerical"
    spec = {
        "q_no": pdf_q,
        "page": (extra or {}).get("page"),
        "booklet": book_id,
        "answer_type": atype,
        "answer_value": value,
        "raw_key": key,
        "figure_keys": [],
        "exam_date": (extra or {}).get("exam_date"),
        "exam_shift": (extra or {}).get("exam_shift"),
    }
    return spec


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = json.loads((OUT / "all_skeleton.json").read_text(encoding="utf-8"))
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)
    holds = []
    for book_id, pdf_q, cont_page, key, kind, paper in JOBS:
        extra = paper if isinstance(paper, dict) else {}
        sk = next((r for r in skeleton if r.get("booklet") == book_id and int(r["q_no"]) == pdf_q), {})
        spec = spec_of(book_id, pdf_q, key, kind, {**sk, **extra})
        spec["page"] = spec.get("page") or sk.get("page") or cont_page
        db = db_rows[(book_id, pdf_q)]
        if extra.get("body"):
            ok, reason = publish_row(sb, db, spec, extra, env, limiter)
            print(f"{book_id} Q{pdf_q} paper {reason}", flush=True)
            if not ok:
                holds.append((book_id, pdf_q, reason))
            continue
        png = OUT / book_id / "crops" / f"top_q{pdf_q:02d}.png"
        print(f"top {book_id} Q{pdf_q} p{cont_page}", flush=True)
        crop_page_top(book_pdf(book_id), cont_page, png)
        data = observe(png, spec, env, limiter)
        raw = pick_question(data, pdf_q) or data
        body = (raw.get("body") or "").strip()
        if body in ("", f"Q{pdf_q}"):
            holds.append((book_id, pdf_q, "empty"))
            print("  empty", flush=True)
            continue
        ok, reason = publish_row(sb, db, spec, {
            "body": body, "options": raw.get("options"), "page": spec["page"],
        }, env, limiter)
        print(f"  {reason}", flush=True)
        if not ok:
            holds.append((book_id, pdf_q, reason))

    dump(OUT / "retry_tops.json", {"holds": holds})
    print("still", holds, flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    sys.exit(main())
