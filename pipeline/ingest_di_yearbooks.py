#!/usr/bin/env python3
"""Publish Definite Integration PYQs from session PDFs onto catalog_slug definite-integration.

Only that chapter. Other chapters in the 2025 books are ignored.
Scoring uses the PDF answer key. glm5.3-flash transcribes the printed page.

    python ingest_di_yearbooks.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import TIEBREAK_MODEL
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from format_ocr_math import format_ocr_math
from ingest_math_2026_jan_definite import BRAND, JEE_SESSION, strip_branding
from publish_math_2026_jan_definite_paper import PAPER as PAPER_2026
from parse_ocr_page import parse_digitise_to_questions

OUT = Path(r"c:\Users\tempo\Downloads\files\out-di-yearbooks")
DPI = 200
SUBJECT = "Mathematics"
CHAPTER_NO = 17

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}

KEY_LINE = re.compile(r"(?:Q\s*)?(\d{1,2})\s*[\.\)]\s*\(?([0-9A-D]+)\)?", re.I)
HEAD_2026 = re.compile(
    r"Q(\d+)\.\s*JEE Main 20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)", re.I)
HEAD_YMD = re.compile(
    r"Q(\d+)\s*[-–]\s*20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)", re.I)
HEAD_DM = re.compile(
    r"Q(\d+)\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s*[-–]\s*Shift\s+([12])", re.I)
HEAD_COLON = re.compile(
    r"Q(\d+)\s*:\s*(\d{1,2})\s+([A-Za-z]+)\s*\(Shift\s+([12])\)", re.I)
HEAD_NUM = re.compile(
    r"(?:^|\n)\s*(\d{1,2})\.\s+.*?\[20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)\]",
    re.I | re.S,
)
HEAD_2020 = re.compile(
    r"(?:Q\s*)?(\d{1,2})\s+(?:(\d{1,2})(?:st|nd|rd|th)?\s+)?Jan(?:uary)?\s+(Morning|Evening)",
    re.I,
)

BOOKLETS = [
    {
        "id": "2020-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\cqb_jm_jan_2020_math_definite_integration.pdf"),
        "year": 2020, "month": 1, "question_pages": (3, 4, 5, 6), "keys": {},
        "style": "2020",
    },
    {
        "id": "2020-sep",
        "pdf": Path(r"C:\Users\tempo\Downloads\definite_integration_questions_jee_main_2020_chapterwise_question_bank_mathongo.pdf"),
        "year": 2020, "month": 9, "question_pages": (1, 2, 3, 4, 5),
        "keys": {
            1: "D", 2: "A", 3: "A", 4: "A", 5: "A", 6: "B", 7: "A",
            8: "1.5", 9: "1", 10: "A", 11: "D", 12: "D", 13: "C",
            14: "21", 15: "D", 16: "B", 17: "B",
        },
        "style": "scan",
    },
    {
        "id": "2021-feb",
        "pdf": Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_february_chapterwiseW7xhGEpjPf0BnZlSz5TE.pdf"),
        "year": 2021, "month": 2, "question_pages": (1, 2, 3, 4),
        "keys": {
            1: "1", 2: "3", 3: "3", 4: "1", 5: "3", 6: "2", 7: "3",
            8: "19", 9: "1", 10: "4", 11: "2", 12: "1", 13: "1", 14: "1",
        },
        "style": "colon",
    },
    {
        "id": "2021-mar",
        "pdf": Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_march_chapterwise_JhLuivAhhuEbSCISHMto.pdf"),
        "year": 2021, "month": 3, "question_pages": (1, 2, 3),
        "keys": {1: "1", 2: "16", 3: "3", 4: "1", 5: "2", 6: "1", 7: "1", 8: "512", 9: "3"},
        "style": "colon",
    },
    {
        "id": "2022-jun",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2022 Chapter wise Questions by MathonGo.pdf"),
        "year": 2022, "month": 6, "question_pages": tuple(range(1, 9)),
        "keys": {
            1: "1", 2: "34", 3: "C", 4: "A", 5: "C", 6: "D", 7: "D", 8: "6", 9: "21", 10: "6",
            11: "3", 12: "D", 13: "B", 14: "A", 15: "C", 16: "B", 17: "C", 18: "D", 19: "D", 20: "C",
        },
        "style": "day-month",
    },
    {
        "id": "2022-jul",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration.pdf"),
        "year": 2022, "month": 7, "question_pages": tuple(range(1, 8)),
        "keys": {
            1: "A", 2: "C", 3: "B", 4: "8", 5: "5", 6: "C", 7: "24", 8: "D", 9: "B", 10: "D",
            11: "B", 12: "385", 13: "12", 14: "A", 15: "10", 16: "A", 17: "104", 18: "B", 19: "D", 20: "A",
        },
        "style": "day-month",
    },
    {
        "id": "2023-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 January Chapter wise Questions by MathonGo.pdf"),
        "year": 2023, "month": 1, "question_pages": tuple(range(1, 10)),
        "keys": {
            1: "22", 2: "2", 3: "4", 4: "27", 5: "1", 6: "3", 7: "4", 8: "20", 9: "1", 10: "2",
            11: "4", 12: "3", 13: "2", 14: "12", 15: "4", 16: "3", 17: "3", 18: "2", 19: "1", 20: "3",
            21: "2", 22: "63", 23: "4", 24: "26",
        },
        "style": "day-month",
    },
    {
        "id": "2023-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 April Chapterwise PYQ - MathonGo.pdf"),
        "year": 2023, "month": 4, "question_pages": (1, 2),
        "keys": {
            1: "3", 2: "0", 3: "14", 4: "6", 5: "3", 6: "1", 7: "32",
            8: "4", 9: "4", 10: "575", 11: "2", 12: "41", 13: "4",
        },
        "style": "bracket",
    },
    {
        "id": "2024-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
        "year": 2024, "month": 1, "question_pages": (1, 2, 3, 4, 5),
        "keys": {
            1: "3", 2: "8", 3: "1", 4: "1", 5: "219", 6: "1", 7: "4", 8: "3", 9: "2", 10: "1",
            11: "6", 12: "2", 13: "155", 14: "2", 15: "4", 16: "176", 17: "27", 18: "5", 19: "3", 20: "15",
        },
        "style": "ymd",
    },
    {
        "id": "2024-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
        "year": 2024, "month": 4, "question_pages": (1, 2, 3, 4),
        "keys": {
            1: "4", 2: "8", 3: "4", 4: "4", 5: "1", 6: "2", 7: "1",
            8: "1", 9: "65", 10: "23", 11: "4", 12: "3", 13: "1", 14: "4",
        },
        "style": "ymd",
    },
    {
        "id": "2025-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "year": 2025, "month": 1, "question_pages": (37, 38, 39),
        "keys": {
            1: "2", 2: "1", 3: "12", 4: "1", 5: "1", 6: "4", 7: "4",
            8: "4", 9: "2", 10: "3", 11: "3", 12: "4", 13: "112",
        },
        "style": "session",
    },
    {
        "id": "2025-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "year": 2025, "month": 4, "question_pages": (37, 38),
        "keys": {1: "1", 2: "3", 3: "8", 4: "1", 5: "2", 6: "1", 7: "4", 8: "4", 9: "3"},
        "style": "session",
    },
    {
        "id": "2026-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf"),
        "year": 2026, "month": 1, "question_pages": (1, 2),
        "keys": {
            1: "9", 2: "2", 3: "3", 4: "2", 5: "2", 6: "36", 7: "3",
            8: "16", 9: "4", 10: "17", 11: "4", 12: "3", 13: "210", 14: "64",
        },
        "style": "2026",
        "paper": PAPER_2026,
    },
]


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def month_num(token: str) -> int:
    return MONTHS[token.strip().lower()[:3] if len(token) > 3 and token[:3].lower() in MONTHS else token.strip().lower()]


def shift_of(token: str) -> str:
    t = token.strip().lower()
    if t in ("2", "evening", "e"):
        return "evening"
    return "morning"


def letter_or_num(val: str) -> tuple[str, str]:
    v = str(val).strip().upper()
    if v in "ABCD":
        return "mcq", str("ABCD".index(v) + 1)
    if v.lstrip("-").isdigit() and 1 <= abs(int(v)) <= 4 and not v.startswith("-") and v != "0":
        return "mcq", v
    return "numerical", str(val).strip()


def parse_headers(book: dict) -> list[dict]:
    doc = pymupdf.open(book["pdf"])
    year = book["year"]
    month = book["month"]
    style = book["style"]
    found: dict[int, dict] = {}
    for pno in book["question_pages"]:
        text = doc[pno - 1].get_text() or ""
        if style == "2026":
            rx, groups = HEAD_2026, "ymd"
        elif style == "ymd":
            rx, groups = HEAD_YMD, "ymd"
        elif style == "day-month":
            rx, groups = HEAD_DM, "dm"
        elif style == "colon":
            rx, groups = HEAD_COLON, "dm"
        elif style == "bracket":
            rx, groups = HEAD_NUM, "br"
        elif style == "2020":
            rx, groups = HEAD_2020, "2020"
        else:
            rx, groups = None, "session"
        if rx is None:
            for m in re.finditer(r"Q(\d+)\.", text):
                q_no = int(m.group(1))
                found.setdefault(q_no, {
                    "q_no": q_no, "page": pno,
                    "exam_date": f"{year}-{month:02d}-01",
                    "exam_shift": None,
                })
            continue
        for m in rx.finditer(text):
            if groups == "ymd":
                q_no = int(m.group(1))
                yy = 2000 + int(m.group(2))
                day = int(m.group(3))
                mo = month_num(m.group(4))
                sh = shift_of(m.group(5))
            elif groups == "dm":
                q_no = int(m.group(1))
                yy = year
                day = int(m.group(2))
                mo = month_num(m.group(3))
                sh = shift_of(m.group(4))
            elif groups == "br":
                q_no = int(m.group(1))
                yy = 2000 + int(m.group(2))
                day = int(m.group(3))
                mo = month_num(m.group(4))
                sh = shift_of(m.group(5))
            else:
                q_no = int(m.group(1))
                yy = year
                day = int(m.group(2) or 1)
                mo = 1
                sh = shift_of(m.group(3))
            found[q_no] = {
                "q_no": q_no, "page": pno,
                "exam_date": f"{yy}-{mo:02d}-{day:02d}",
                "exam_shift": sh,
            }
    doc.close()
    for q_no in book.get("keys") or []:
        found.setdefault(int(q_no), {
            "q_no": int(q_no),
            "page": book["question_pages"][0],
            "exam_date": f"{year}-{month:02d}-01",
            "exam_shift": None,
        })
    if not found and book.get("keys"):
        first_page = book["question_pages"][0]
        for q_no in book["keys"]:
            found[q_no] = {
                "q_no": q_no, "page": first_page,
                "exam_date": f"{year}-{month:02d}-01",
                "exam_shift": None,
            }
    rows = []
    for q_no, rec in sorted(found.items()):
        raw = book.get("keys", {}).get(q_no)
        kind, value = letter_or_num(raw) if raw is not None else ("numerical", "")
        rec.update({
            "booklet": book["id"],
            "answer_type": kind,
            "answer_value": value,
            "raw_key": raw,
            "figure_keys": [],
        })
        rows.append(rec)
    return rows


def rasterize(book: dict) -> Path:
    dest_dir = OUT / book["id"] / "pages"
    dest_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    zoom = DPI / 72
    mat = pymupdf.Matrix(zoom, zoom)
    for pno in book["question_pages"]:
        dest = dest_dir / f"page_{pno:03d}.png"
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        pix = doc[pno - 1].get_pixmap(matrix=mat, alpha=False)
        pix.save(str(dest))
        print(f"raster {book['id']} {dest.name}", flush=True)
    doc.close()
    return dest_dir


def transcribe_page(book: dict, page_no: int, slice_: list, env: dict, limiter: p.RateLimiter) -> dict:
    cache = OUT / book["id"] / "parsed" / f"page_{page_no:03d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    p.OUT = OUT / book["id"]
    payload = p.digitise_page(page_no, env["SARVAM_API_KEY"])
    slice_p = [{**rec, "figure_keys": rec.get("figure_keys") or []} for rec in slice_]
    questions = parse_digitise_to_questions(payload, slice_p)
    data = {"questions": questions}
    dump(cache, data)
    return data


def clean_entry(entry: dict, spec: dict) -> dict:
    body = format_ocr_math(strip_branding(entry.get("body") or ""))
    body = re.sub(r"\bM\.\s*", " ", body)
    body = re.sub(r"[ \t]{2,}", " ", body).strip()
    options = entry.get("options")
    if isinstance(options, list) and len(options) == 4:
        options = [re.sub(r"\bM\.\s*", " ", format_ocr_math(strip_branding(o or ""))) for o in options]
        options = [re.sub(r"[ \t]{2,}", " ", o).strip() for o in options]
    else:
        options = None
    if spec["answer_type"] != "mcq":
        options = None
    return {"body": body, "options": options, "page": spec["page"]}


def refine_type(spec: dict, entry: dict) -> dict:
    raw = spec.get("raw_key")
    opts = entry.get("options")
    has_mcq = isinstance(opts, list) and len(opts) == 4 and all((o or "").strip() for o in opts)
    if raw is None or raw == "":
        spec["answer_type"] = "mcq" if has_mcq else "numerical"
        return spec
    v = str(raw).strip().upper()
    if v in "ABCD":
        spec["answer_type"] = "mcq"
        spec["answer_value"] = str("ABCD".index(v) + 1)
        return spec
    if has_mcq and v.isdigit() and 1 <= int(v) <= 4:
        spec["answer_type"] = "mcq"
        spec["answer_value"] = v
        if spec["answer_type"] != "mcq":
            entry["options"] = None
        return spec
    spec["answer_type"] = "numerical"
    spec["answer_value"] = str(raw).strip()
    entry["options"] = None
    return spec


def seed_chapter(sb) -> int:
    return p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    env = p.load_env()
    limiter = p.RateLimiter(60)
    all_rows: list[dict] = []
    parsed: dict[tuple[str, int], dict] = {}

    for book in BOOKLETS:
        if not book["pdf"].is_file():
            raise SystemExit(f"missing {book['pdf']}")
        print(f"booklet {book['id']}", flush=True)
        rasterize(book)
        rows = parse_headers(book)
        if not rows and book["style"] in ("scan", "2020"):
            rows = [{
                "q_no": i + 1, "page": pno, "booklet": book["id"],
                "exam_date": f"{book['year']}-{book['month']:02d}-01",
                "exam_shift": None, "answer_type": "mcq", "answer_value": "",
                "raw_key": None, "figure_keys": [],
            } for i, pno in enumerate(book["question_pages"])]
        dump(OUT / book["id"] / "skeleton.json", rows)
        by_page: dict[int, list] = {}
        for rec in rows:
            by_page.setdefault(rec["page"], []).append(rec)

        paper = book.get("paper")
        for page_no, slice_ in by_page.items():
            if paper:
                for rec in slice_:
                    item = paper.get(rec["q_no"]) or {}
                    parsed[(book["id"], rec["q_no"])] = {
                        "body": item.get("body") or "",
                        "options": item.get("options"),
                        "page": page_no,
                    }
                continue
            print(f"  vision {book['id']} p{page_no} ({len(slice_)} q)", flush=True)
            try:
                data = transcribe_page(book, page_no, slice_, env, limiter)
            except Exception as exc:
                dump(OUT / book["id"] / "vision" / f"page_{page_no:03d}.error.json",
                     {"error": f"{type(exc).__name__}: {exc}"})
                data = {"questions": []}
            by_q = {int(q["q_no"]): q for q in (data.get("questions") or []) if "q_no" in q}
            for rec in slice_:
                q = by_q.get(rec["q_no"]) or {}
                parsed[(book["id"], rec["q_no"])] = clean_entry({
                    "body": q.get("body") or "",
                    "options": q.get("options"),
                    "page": page_no,
                }, rec)
        all_rows.extend(rows)

    all_rows.sort(key=lambda r: (
        r.get("exam_date") or "9999-99-99",
        0 if r.get("exam_shift") == "morning" else 1 if r.get("exam_shift") == "evening" else 2,
        r["booklet"],
        r["q_no"],
    ))
    for i, rec in enumerate(all_rows, start=1):
        rec["db_q_no"] = i

    dump(OUT / "all_skeleton.json", all_rows)
    print(f"total questions {len(all_rows)}", flush=True)

    sb = p.supabase_client()
    chapter_id = seed_chapter(sb)
    existing = (
        sb.table("pyq_questions").select("id").eq("chapter_id", chapter_id).execute().data or []
    )
    if existing:
        sb.table("pyq_questions").delete().eq("chapter_id", chapter_id).execute()
        print(f"cleared {len(existing)} old math DI rows", flush=True)

    seed = []
    for rec in all_rows:
        seed.append({
            "chapter_id": chapter_id,
            "topic_id": None,
            "q_no": rec["db_q_no"],
            "tier": "must_do",
            "format": rec["answer_type"],
            "body": None,
            "correct_option": int(rec["answer_value"]) if rec["answer_type"] == "mcq" and str(rec["answer_value"]).isdigit() else None,
            "numerical_answer": None if rec["answer_type"] == "mcq" else (rec["answer_value"] or None),
            "exam_date": rec["exam_date"],
            "exam_shift": rec["exam_shift"],
            "out_of_syllabus": False,
            "good_to_solve": False,
            "source_page": rec["page"],
            "source_bbox": {"booklet": rec["booklet"], "pdf_q": rec["q_no"]},
            "review_status": "skeleton_only",
        })
    sb.table("pyq_questions").insert(seed).execute()
    fetched = (
        sb.table("pyq_questions").select("id,q_no")
        .eq("chapter_id", chapter_id).execute().data
    )
    q_ids = {int(r["q_no"]): r["id"] for r in fetched}

    holds = []
    live = 0
    for rec in all_rows:
        entry = parsed.get((rec["booklet"], rec["q_no"])) or {"body": "", "options": None}
        rec = refine_type(rec, entry)
        entry = clean_entry(entry, rec)
        db_id = q_ids[rec["db_q_no"]]
        shape_ok = shape_ok_for(rec, entry)
        audit_ok = not flags_for(entry.get("body") or "", is_option=False)
        if entry.get("options"):
            audit_ok = audit_ok and all(not flags_for(o or "", is_option=True) for o in entry["options"])
        katex_ok = False
        if entry.get("body"):
            fields = [entry["body"]] + (entry.get("options") or [])
            katex_ok = all(katex_render_ok(t) for t in fields)
        solver_dump = is_solver_dump(entry.get("body") or "")
        key = rec.get("answer_value") or rec.get("raw_key")
        publishable = (
            shape_ok and audit_ok and katex_ok and not solver_dump
            and key not in (None, "")
        )
        status = "human_ok" if publishable else "unreviewed"
        if status == "human_ok":
            live += 1
        else:
            holds.append({
                "booklet": rec["booklet"], "pdf_q": rec["q_no"], "db_q": rec["db_q_no"],
                "shape_ok": shape_ok, "audit_ok": audit_ok, "katex_ok": katex_ok,
                "key": key, "preview": (entry.get("body") or "")[:120],
            })
        upsert_question(
            sb, db_id, entry, status,
            1.0 if status == "human_ok" else 0.5,
            rec,
            answer=str(key) if status == "human_ok" else None,
        )

    sb.table("pyq_chapters").update({"expected_question_count": len(all_rows)}).eq("id", chapter_id).execute()
    dump(OUT / "hold.json", holds)
    print(f"live {live}/{len(all_rows)} holds {len(holds)}", flush=True)
    for h in holds[:40]:
        print(f"  hold {h['booklet']} Q{h['pdf_q']} katex={h['katex_ok']} shape={h['shape_ok']}", flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    sys.exit(main())
