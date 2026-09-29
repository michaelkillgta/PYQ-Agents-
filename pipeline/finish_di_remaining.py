#!/usr/bin/env python3
"""Finish held Definite Integration rows and the missing 2020 chapterwise papers.

Scoring uses printed PDF keys only. One-question vision to avoid truncated JSON.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok, needs_llm_wrap
from agents.models import PRIMARY_SOLVER, TIEBREAK_MODEL, VISION_MODEL
from agents.publish import shape_ok_for
from agents.solvers import parse_mcq_choice
from audit_paper_text import flags_for
from ingest_di_yearbooks import (
    BOOKLETS,
    CHAPTER_NO,
    OUT,
    SUBJECT,
    clean_entry,
    dump,
    rasterize,
    refine_type,
)
from ingest_math_2026_jan_definite import strip_branding
from run_chapter_agents import OBSERVER_SYSTEM, WRAP_SYSTEM, v2_json

HINDI = re.compile(r"[\u0900-\u097F]")
DEVANAGARI_LINE = re.compile(r"[\u0900-\u097F]")

SEP_KEYS = {
    1: "D", 2: "A", 3: "A", 4: "A", 5: "A", 6: "B", 7: "A",
    8: "1.5", 9: "1", 10: "A", 11: "D", 12: "D", 13: "C",
    14: "21", 15: "D", 16: "B", 17: "B",
}
SEP_META = {
    1: (1, "2020-01-07", "morning"),
    2: (1, "2020-01-07", "evening"),
    3: (1, "2020-01-07", "evening"),
    4: (1, "2020-01-08", "evening"),
    5: (2, "2020-01-09", "morning"),
    6: (2, "2020-01-09", "morning"),
    7: (2, "2020-01-09", "morning"),
    8: (2, "2020-09-02", "morning"),
    9: (2, "2020-09-02", "evening"),
    10: (3, "2020-09-03", "morning"),
    11: (3, "2020-09-03", "evening"),
    12: (3, "2020-09-04", "morning"),
    13: (3, "2020-09-04", "evening"),
    14: (3, "2020-09-04", "evening"),
    15: (4, "2020-09-05", "morning"),
    16: (4, "2020-09-06", "morning"),
    17: (4, "2020-09-06", "evening"),
}

ONE_Q = [
    ("2021-mar", 9, (2, 3)),
    ("2022-jun", 4, (1,)),
    ("2022-jun", 18, (6, 7)),
    ("2022-jul", 3, (1,)),
    ("2022-jul", 6, (2,)),
    ("2022-jul", 11, (4,)),
    ("2022-jul", 14, (5,)),
    ("2023-jan", 6, (2,)),
    ("2023-jan", 12, (4,)),
    ("2023-jan", 20, (7,)),
    ("2023-apr", 11, (2,)),
    ("2024-apr", 10, (2,)),
    ("2025-jan", 9, (38,)),
]


def book_by_id(book_id: str) -> dict:
    for book in BOOKLETS:
        if book["id"] == book_id:
            return book
    raise KeyError(book_id)


def strip_hindi(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        letters = re.findall(r"[A-Za-z\u0900-\u097F]", line)
        hin = DEVANAGARI_LINE.findall(line)
        if letters and len(hin) / max(len(letters), 1) > 0.35:
            continue
        lines.append(HINDI.sub("", line))
    return re.sub(r"[ \t]{2,}", " ", "\n".join(lines)).strip()


def local_katex_fix(text: str) -> str:
    s = text or ""
    s = s.replace("$x ext{ } ext{R}$", r"$x \in \mathbb{R}$")
    s = s.replace("x ext{ } ext{R}", r"$x \in \mathbb{R}$")
    s = s.replace(r"$ ext{ } ext{∫}", r"$\int")
    s = s.replace("ext{ } ext{", r"\text{")
    s = re.sub(r"\$2\\pi(?!\$)", r"$2\\pi$", s)
    return s


def wrap_text(text: str, env: dict, limiter: p.RateLimiter) -> str:
    s = local_katex_fix(strip_hindi(strip_branding(text or "")))
    if not needs_llm_wrap(s) and katex_render_ok(s):
        return s
    messages = [
        {"role": "system", "content": WRAP_SYSTEM},
        {"role": "user", "content": s},
    ]
    try:
        data = v2_json(PRIMARY_SOLVER, messages, env, limiter)
        out = str(data.get("text") or s)
        return out if katex_render_ok(out) else s
    except Exception:
        return s


def transcribe_one(book_id: str, pdf_q: int, page_no: int, spec: dict,
                   env: dict, limiter: p.RateLimiter) -> dict:
    cache = OUT / book_id / "gemma4" / f"q{pdf_q:02d}_p{page_no:03d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    png = OUT / book_id / "pages" / f"page_{page_no:03d}.png"
    if not png.exists():
        raise FileNotFoundError(png)
    prompt = (
        f"Transcribe ONLY printed question Q{pdf_q} on this page. "
        "Ignore solutions, other questions, Hindi duplicate lines, and branding. "
        "KaTeX with $...$. Do not solve. "
        "If four options are printed, return them. "
        "If the printed Sol box shows (1)/(2)/(3)/(4) or A/B/C/D, copy that as printed_key.\n"
        + json.dumps({"q_no": pdf_q, "answer_type": spec.get("answer_type")}, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": OBSERVER_SYSTEM}]
    messages.extend(p.page_image_message(png, prompt))
    try:
        data = v2_json(TIEBREAK_MODEL, messages, env, limiter)
        data["_model"] = TIEBREAK_MODEL
    except Exception as exc:
        print(f"    flash fail {type(exc).__name__}, gemma4", flush=True)
        data = v2_json(VISION_MODEL, messages, env, limiter)
        data["_model"] = VISION_MODEL
    dump(cache, data)
    return data


def pick_question(data: dict, pdf_q: int) -> dict:
    for q in data.get("questions") or []:
        try:
            if int(q.get("q_no")) == pdf_q:
                return q
        except (TypeError, ValueError):
            continue
    if isinstance(data.get("body"), str):
        return data
    return {}


def audit_ok(entry: dict) -> bool:
    hits = flags_for(entry.get("body") or "", is_option=False)
    for opt in entry.get("options") or []:
        hits.extend(flags_for(opt or "", is_option=True))
    return not [h for h in hits if not str(h).startswith("empty")]


def wrap_entry(entry: dict, env: dict, limiter: p.RateLimiter) -> dict:
    body = wrap_text(entry.get("body") or "", env, limiter)
    opts = entry.get("options")
    if isinstance(opts, list) and len(opts) == 4:
        opts = [wrap_text(o, env, limiter) for o in opts]
    else:
        opts = None
    return {"body": body, "options": opts, "page": entry.get("page")}


def publish_row(sb, db: dict, spec: dict, entry: dict, env: dict,
                limiter: p.RateLimiter) -> tuple[bool, str]:
    spec = dict(spec)
    raw_entry = {
        "body": strip_hindi(entry.get("body") or ""),
        "options": entry.get("options"),
        "page": entry.get("page"),
    }
    spec = refine_type(spec, raw_entry)
    entry = clean_entry(raw_entry, spec)
    fields = [entry.get("body") or ""] + (entry.get("options") or [])
    if entry.get("body") and not all(katex_render_ok(t) for t in fields):
        entry = wrap_entry(entry, env, limiter)
        spec = refine_type(spec, entry)
        entry = {
            "body": entry.get("body") or "",
            "options": entry.get("options"),
            "page": entry.get("page"),
        }
    key = spec.get("answer_value") or spec.get("raw_key")
    fields = [entry.get("body") or ""] + (entry.get("options") or [])
    katex_ok = all(katex_render_ok(t) for t in fields) if entry.get("body") else False
    shape = shape_ok_for(spec, entry)
    ok = (
        shape and audit_ok(entry) and katex_ok
        and not is_solver_dump(entry.get("body") or "")
        and key not in (None, "")
    )
    patch = {
        "body": (entry.get("body") or "").strip() or None,
        "format": spec["answer_type"],
        "extraction_confidence": 1.0 if ok else 0.5,
        "review_status": "human_ok" if ok else "unreviewed",
        "source_page": spec.get("page") or db.get("source_page"),
        "source_bbox": {
            **(db.get("source_bbox") or {}),
            "booklet": spec["booklet"],
            "pdf_q": spec["q_no"],
        },
    }
    if spec.get("exam_date"):
        patch["exam_date"] = spec["exam_date"]
    if spec.get("exam_shift"):
        patch["exam_shift"] = spec["exam_shift"]
    if spec["answer_type"] == "mcq":
        choice = parse_mcq_choice(str(key)) if key not in (None, "") else None
        patch["correct_option"] = choice
        patch["numerical_answer"] = None
    else:
        patch["correct_option"] = None
        patch["numerical_answer"] = str(key).strip() if ok else (str(key).strip() if key else None)
        if not ok:
            patch["numerical_answer"] = str(key).strip() if key not in (None, "") else None
    if not ok:
        patch["correct_option"] = patch.get("correct_option")
        if spec["answer_type"] == "mcq":
            patch["numerical_answer"] = None
    sb.table("pyq_questions").update(patch).eq("id", db["id"]).execute()
    qid = db["id"]
    if spec["answer_type"] == "mcq" and entry.get("options"):
        sb.table("pyq_question_options").upsert(
            [
                {"question_id": qid, "option_index": i, "body": text}
                for i, text in enumerate(entry["options"], start=1)
            ],
            on_conflict="question_id,option_index",
        ).execute()
    elif spec["answer_type"] != "mcq":
        sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
    reason = "ok" if ok else (
        f"shape={shape} audit={audit_ok(entry)} katex={katex_ok} key={key!r}"
    )
    return ok, reason


def fetch_rows(sb, chapter_id: int) -> dict[tuple[str, int], dict]:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,review_status,format,source_bbox,source_page,exam_date,exam_shift,body")
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


def spec_from_skeleton(skeleton: list[dict], book_id: str, pdf_q: int) -> dict:
    for rec in skeleton:
        if rec.get("booklet") == book_id and int(rec["q_no"]) == pdf_q:
            return dict(rec)
    raise KeyError((book_id, pdf_q))


def ensure_sep_rows(sb, chapter_id: int, db_rows: dict) -> dict:
    existing = {k: v for k, v in db_rows.items() if k[0] == "2020-sep"}
    max_q = max((row["q_no"] for row in db_rows.values()), default=0)
    seed = []
    for pdf_q, (page, date, shift) in SEP_META.items():
        raw = SEP_KEYS[pdf_q]
        kind = "mcq" if str(raw).strip().upper() in "ABCD" else "numerical"
        value = str("ABCD".index(raw.strip().upper()) + 1) if kind == "mcq" else str(raw)
        spec = {
            "q_no": pdf_q,
            "page": page,
            "exam_date": date,
            "exam_shift": shift,
            "booklet": "2020-sep",
            "answer_type": kind,
            "answer_value": value,
            "raw_key": raw,
            "figure_keys": [],
        }
        if ( "2020-sep", pdf_q) in existing:
            continue
        max_q += 1
        seed.append({
            "chapter_id": chapter_id,
            "topic_id": None,
            "q_no": max_q,
            "tier": "must_do",
            "format": kind,
            "body": None,
            "correct_option": int(value) if kind == "mcq" else None,
            "numerical_answer": None if kind == "mcq" else value,
            "exam_date": date,
            "exam_shift": shift,
            "out_of_syllabus": False,
            "good_to_solve": False,
            "source_page": page,
            "source_bbox": {"booklet": "2020-sep", "pdf_q": pdf_q},
            "review_status": "skeleton_only",
        })
        print(f"  insert 2020-sep Q{pdf_q} as q_no {max_q}", flush=True)
    if seed:
        sb.table("pyq_questions").insert(seed).execute()
        return fetch_rows(sb, chapter_id)
    return db_rows


def vision_and_publish(sb, db: dict, spec: dict, pages: tuple[int, ...],
                       env: dict, limiter: p.RateLimiter) -> tuple[bool, str]:
    last = "no-vision"
    for page_no in pages:
        spec = dict(spec)
        spec["page"] = page_no
        try:
            data = transcribe_one(spec["booklet"], spec["q_no"], page_no, spec, env, limiter)
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
            print(f"  vision fail {spec['booklet']} Q{spec['q_no']} p{page_no} {last}", flush=True)
            continue
        raw = pick_question(data, spec["q_no"])
        body = (raw.get("body") or "").strip()
        if not body:
            last = "empty-body"
            continue
        printed = raw.get("printed_key")
        if printed and not spec.get("raw_key"):
            spec["raw_key"] = str(printed)
            if str(printed).strip().upper() in "ABCD":
                spec["answer_type"] = "mcq"
                spec["answer_value"] = str("ABCD".index(str(printed).strip().upper()) + 1)
            elif str(printed).strip() in "1234":
                spec["answer_type"] = "mcq"
                spec["answer_value"] = str(printed).strip()
        ok, reason = publish_row(sb, db, spec, {
            "body": body,
            "options": raw.get("options"),
            "page": page_no,
        }, env, limiter)
        print(f"  {spec['booklet']} Q{spec['q_no']} p{page_no} {reason}", flush=True)
        if ok:
            return True, reason
        last = reason
    return False, last


def fix_2025_jan_q9(sb, db: dict, spec: dict, env: dict, limiter: p.RateLimiter) -> bool:
    body = (
        r"Let $f(x) = 7\tan^8 x + 7\tan^6 x - 3\tan^4 x - 3\tan^2 x$, "
        r"$I_1 = \int_{0}^{\pi/4} f(x)\, dx$ and $I_2 = \int_{0}^{\pi/4} x f(x)\, dx$. "
        r"Then $7I_1 + 12I_2$ is equal to :"
    )
    options = ["1", "2", r"$2\pi$", r"$\pi$"]
    ok, reason = publish_row(sb, db, spec, {
        "body": body, "options": options, "page": spec["page"],
    }, env, limiter)
    print(f"  2025-jan Q9 local {reason}", flush=True)
    return ok


def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    for book in BOOKLETS:
        if book["id"] in {"2020-sep", "2020-jan", "2021-mar", "2022-jun", "2022-jul",
                          "2023-jan", "2023-apr", "2024-apr", "2025-jan"}:
            rasterize(book)

    skeleton = json.loads((OUT / "all_skeleton.json").read_text(encoding="utf-8"))
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)
    db_rows = ensure_sep_rows(sb, chapter_id, db_rows)

    live = []
    holds = []

    print("2020-sep all 17", flush=True)
    for pdf_q, (page, date, shift) in SEP_META.items():
        raw = SEP_KEYS[pdf_q]
        kind = "mcq" if str(raw).strip().upper() in "ABCD" else "numerical"
        value = str("ABCD".index(raw.strip().upper()) + 1) if kind == "mcq" else str(raw)
        spec = {
            "q_no": pdf_q,
            "page": page,
            "exam_date": date,
            "exam_shift": shift,
            "booklet": "2020-sep",
            "answer_type": kind,
            "answer_value": value,
            "raw_key": raw,
            "figure_keys": [],
        }
        db = db_rows[("2020-sep", pdf_q)]
        ok, reason = vision_and_publish(sb, db, spec, (page,), env, limiter)
        (live if ok else holds).append(("2020-sep", pdf_q, reason))

    for book_id, pdf_q, pages in ONE_Q:
        spec = spec_from_skeleton(skeleton, book_id, pdf_q)
        db = db_rows.get((book_id, pdf_q))
        if db is None:
            holds.append((book_id, pdf_q, "missing-row"))
            continue
        if book_id == "2025-jan" and pdf_q == 9:
            if fix_2025_jan_q9(sb, db, spec, env, limiter):
                live.append((book_id, pdf_q, "local"))
                continue
        print(f"held {book_id} Q{pdf_q}", flush=True)
        ok, reason = vision_and_publish(sb, db, spec, pages, env, limiter)
        (live if ok else holds).append((book_id, pdf_q, reason))

    dump(OUT / "finish_remaining.json", {"live": live, "holds": holds})
    print(f"published {len(live)} still_held {len(holds)}", flush=True)
    for item in holds:
        print(f"  HOLD {item}", flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    sys.exit(main())
