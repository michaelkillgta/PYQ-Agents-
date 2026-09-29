#!/usr/bin/env python3
"""No-miss OCR inventory for MathonGo chapter-wise / session PYQ PDFs.

Every printed `Q n.` heading on the questions half must have an Answer Keys
line for that chapter. Titles are matched on the **full page** (they often sit
in the footer). Compact Answer Keys can span several pages — concatenate them.
TOC page numbers are not question counts.

    python pyq_ocr_inventory.py --pdf PATH
    python pyq_ocr_inventory.py --pdf PATH --titles "Definite Integration,Area Under Curves"
    python pyq_ocr_inventory.py --pdf PATH --titles "..." --crop-dir DIR
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pymupdf

Q_LINE = re.compile(r"^Q\s*(\d+)\s*\.\s*")
Q_LEAD = re.compile(r"^Q\s*\d+")
SOL_Q_HEAD = re.compile(
    r"^Q\s*(\d+)\s*\.\s*(?:\(\s*([^)]+?)\s*\))?(?:\s.*)?$"
)
SOL_KEY_NEAR = re.compile(r"^\(\s*(\d+)\s*\)")
SESSION_Q = re.compile(r"^Q\s*(\d+)(?:\s*$|\s*[-–:])", re.I)
NUM_Q_LINE = re.compile(r"^(\d{1,2})\.(?:\s|$)")
SESSION_KEY = re.compile(r"Q\s*(\d+)\s*\(\s*([^)]+?)\s*\)", re.I)
ANSWER_KEY_HEAD = re.compile(r"^\s*answer\s*keys?\s*$", re.I)
ANSWERS_SOLUTIONS_HEAD = re.compile(r"^\s*answers?\s+and\s+solutions?\s*$", re.I)
# Compact strip: `1. 9` or `2. (2)`. Worked write-ups are `1. (9) Let …`.
COMPACT_KEY_LINE = re.compile(r"^(\d{1,2})\.\s+(\(?[0-9A-Da-d]+\)?)\s*$")
SOL_HEAD_LINE = re.compile(r"^(\d{1,2})\.\s*\(([^)]+)\)")
KEY_ITEM = re.compile(r"(\d{1,2})\s*\.\s*\(([^)]+)\)")
DPI = 200

# Printed TOC titles in 2025 January / April chapter-wise books (29 chapters).
# Not the 33-chapter 2019–2025 compilation (no Mathematical Reasoning / Differentiation
# / Heights and Distances / Properties of Triangles).
MATH_CHAPTER_TITLES: tuple[str, ...] = (
    "Basic of Mathematics",
    "Quadratic Equation",
    "Complex Number",
    "Sequences and Series",
    "Permutation Combination",
    "Binomial Theorem",
    "Statistics",
    "Matrices",
    "Determinants",
    "Probability",
    "Sets and Relations",
    "Functions",
    "Limits",
    "Continuity and Differentiability",
    "Application of Derivatives",
    "Indefinite Integration",
    "Definite Integration",
    "Area Under Curves",
    "Differential Equations",
    "Straight Lines",
    "Circle",
    "Parabola",
    "Ellipse",
    "Hyperbola",
    "Trigonometric Ratios & Identities",
    "Trigonometric Equations",
    "Inverse Trigonometric Functions",
    "Vector Algebra",
    "Three Dimensional Geometry",
)

# Question-page footers sometimes shorten a TOC title. Still the same chapter.
MATH_TITLE_ALIASES: dict[str, str] = {
    "Trigonometric Ratios": "Trigonometric Ratios & Identities",
}

_TITLE_RX = [
    (title, re.compile(rf"^{re.escape(title)}$", re.I))
    for title in MATH_CHAPTER_TITLES
]
_TITLE_ORDER = {t: i for i, t in enumerate(MATH_CHAPTER_TITLES)}


def page_text(page) -> str:
    return page.get_text("text") or ""


def nonempty_lines(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.strip().replace("\xa0", " ").strip()
        if line:
            out.append(line)
    return out


def is_compact_key_page(text: str) -> bool:
    """Answer-key listing (Title + `1. (2)`), not the worked-solutions half."""
    lines = nonempty_lines(text)
    if not lines or not KEY_ITEM.search(text):
        return False
    if Q_LEAD.match(lines[0]):
        return False
    return any(rx.fullmatch(line) for line in lines for _title, rx in _TITLE_RX)


def compact_key_pages(doc) -> list[int]:
    pages: list[int] = []
    started = False
    for i in range(doc.page_count):
        text = page_text(doc[i])
        if is_compact_key_page(text):
            started = True
            pages.append(i + 1)
            continue
        if started:
            break
    return pages


def find_key_page(doc) -> int | None:
    pages = compact_key_pages(doc)
    return pages[0] if pages else None


def concatenated_key_text(doc) -> str:
    return "\n".join(page_text(doc[p - 1]) for p in compact_key_pages(doc))


def canonical_running_title(line: str) -> str | None:
    raw = line.strip().replace("\xa0", " ").strip()
    if not raw:
        return None
    alias = MATH_TITLE_ALIASES.get(raw)
    if alias:
        return alias
    for title, rx in _TITLE_RX:
        if rx.fullmatch(raw):
            return title
    return None


def page_chapter_title(page) -> str | None:
    """Match a chapter title on any line of the page, not the first N lines."""
    text = page_text(page)
    found: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        title = canonical_running_title(line)
        if title and title not in seen:
            seen.add(title)
            found.append(title)
    if not found:
        return None
    if "Indefinite Integration" in found and "Definite Integration" in found:
        found = [t for t in found if t != "Definite Integration"]
    return min(found, key=lambda t: _TITLE_ORDER.get(t, 999))


def q_anchors(page) -> list[dict]:
    anchors = []
    width = page.rect.width
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            txt = "".join(s.get("text") or "" for s in line.get("spans") or []).strip()
            m = Q_LINE.match(txt)
            if not m:
                continue
            x0, y0, _x1, y1 = line["bbox"]
            if x0 > width * 0.55:
                continue
            anchors.append({"q_no": int(m.group(1)), "y0": y0, "y1": y1})
    anchors.sort(key=lambda a: a["y0"])
    dedup = []
    seen = set()
    for a in anchors:
        if a["q_no"] in seen:
            continue
        seen.add(a["q_no"])
        dedup.append(a)
    return dedup


def _title_needles(title: str) -> list[str]:
    needles = [title]
    for alias, canonical in MATH_TITLE_ALIASES.items():
        if canonical.lower() == title.lower() and alias not in needles:
            needles.append(alias)
    return needles


def parse_section_keys(text: str, title: str, following: list[str] | tuple[str, ...] | str | None) -> dict[int, str]:
    """Keys from this chapter heading until the next heading that is actually printed.

    April 2025 skips Trigonometric Ratios between Hyperbola and Trigonometric
    Equations, so stopping only on the immediate TOC neighbor swallows later keys.
    """
    low = text.lower()
    start = low.find(title.lower())
    if start < 0:
        return {}
    chunk = text[start:]
    if isinstance(following, str):
        later = [following]
    else:
        later = list(following or [])
    stop_at = None
    for cand in later:
        for needle in _title_needles(cand):
            stop = chunk.lower().find(needle.lower(), len(title))
            if stop > 0 and (stop_at is None or stop < stop_at):
                stop_at = stop
        if stop_at is not None:
            break
    if stop_at:
        chunk = chunk[:stop_at]
    keys = {}
    for m in KEY_ITEM.finditer(chunk):
        keys[int(m.group(1))] = m.group(2).strip()
    return keys


def inventory_pdf(pdf: Path, titles: list[str] | None = None) -> dict:
    """Return per-chapter printed Qs vs answer-key lines. gate_ok iff they match."""
    doc = pymupdf.open(pdf)
    key_pages = compact_key_pages(doc)
    key_page = key_pages[0] if key_pages else None
    key_text = concatenated_key_text(doc)
    end = key_page or (doc.page_count + 1)
    by_title: dict[str, dict] = {
        title: {"title": title, "pages": [], "questions": [], "keys": {}}
        for title in MATH_CHAPTER_TITLES
    }
    for i in range(min(end - 1, doc.page_count)):
        page = doc[i]
        title = page_chapter_title(page)
        if not title:
            continue
        rec = by_title[title]
        rec["pages"].append(i + 1)
        for a in q_anchors(page):
            rec["questions"].append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
            })
    for idx, title in enumerate(MATH_CHAPTER_TITLES):
        later = list(MATH_CHAPTER_TITLES[idx + 1:])
        by_title[title]["keys"] = parse_section_keys(key_text, title, later)
    doc.close()

    want = [t.strip() for t in titles] if titles else [
        t for t, rec in by_title.items() if rec["questions"] or rec["keys"]
    ]
    chapters = []
    for title in want:
        rec = by_title.get(title) or {"title": title, "pages": [], "questions": [], "keys": {}}
        printed = sorted({q["q_no"] for q in rec["questions"]})
        keys = rec["keys"]
        plan = crop_plan(rec)
        gate_ok = printed == sorted(keys) and len(printed) > 0 and len(plan) == len(printed)
        chapters.append({
            "title": title,
            "pages": rec["pages"],
            "questions": rec["questions"],
            "printed": printed,
            "printed_count": len(printed),
            "keys": keys,
            "key_count": len(keys),
            "crop_plan": plan,
            "crop_count": len(plan),
            "gate_ok": gate_ok,
        })
    return {
        "pdf": str(pdf),
        "key_page": key_page,
        "key_pages": key_pages,
        "questions_end_page": end,
        "chapters": chapters,
        "printed_total": sum(c["printed_count"] for c in chapters),
        "key_total": sum(c["key_count"] for c in chapters),
        "crop_total": sum(c["crop_count"] for c in chapters),
        "gate_ok": all(c["gate_ok"] for c in chapters) and len(chapters) > 0,
    }


def crop_plan(chapter: dict) -> list[dict]:
    """One crop spec per printed Q. Continuation stays on the same running title."""
    qs = sorted(chapter.get("questions") or [], key=lambda q: (q["page"], q["y0"], q["q_no"]))
    seen = set()
    unique = []
    for rec in qs:
        if rec["q_no"] in seen:
            continue
        seen.add(rec["q_no"])
        unique.append(rec)
    by_page: dict[int, list[dict]] = {}
    for rec in unique:
        by_page.setdefault(rec["page"], []).append(rec)
    pages = set(chapter.get("pages") or [])
    plan = []
    for rec in unique:
        later = [
            a for a in by_page.get(rec["page"], [])
            if a["q_no"] > rec["q_no"] and a["y0"] > rec["y0"] + 4
        ]
        continuation = None
        if not later:
            nxt = rec["page"] + 1
            if nxt in pages:
                nxt_anchors = by_page.get(nxt, [])
                cut_y = min((a["y0"] for a in nxt_anchors), default=None)
                continuation = {"page": nxt, "cut_y": cut_y}
        clip_y1 = (min(a["y0"] for a in later) - 4) if later else None
        plan.append({
            "page": rec["page"],
            "q_no": rec["q_no"],
            "y0": rec["y0"],
            "y1": rec["y1"],
            "clip_y1": clip_y1,
            "heading": rec.get("heading") or "",
            "later_same_page": bool(later),
            "continues": continuation is not None,
            "continuation": continuation,
        })
    return plan


def stitch(pixes: list, dest: Path) -> Path:
    w = max(px.width for px in pixes)
    h = sum(px.height for px in pixes)
    out = pymupdf.Pixmap(pixes[0].colorspace, pymupdf.IRect(0, 0, w, h), pixes[0].alpha)
    out.clear_with(255)
    y = 0
    for pix in pixes:
        src = pix
        if src.width < w:
            padded = pymupdf.Pixmap(
                src.colorspace, pymupdf.IRect(0, y, src.width, y + src.height), src.alpha
            )
            padded.clear_with(255)
            src.set_origin(0, y)
            padded.copy(src, src.irect)
            src = padded
        else:
            src.set_origin(0, y)
        out.copy(src, src.irect)
        y += pix.height
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(dest))
    return dest


def render_crop(doc, spec: dict, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    page = doc[spec["page"] - 1]
    y0 = max(page.rect.y0 + 6, spec["y0"] - 8)
    scale = pymupdf.Matrix(DPI / 72, DPI / 72)
    if spec.get("clip_y1") is not None:
        y1 = max(float(spec["clip_y1"]), y0 + 40)
        clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
        pix = page.get_pixmap(matrix=scale, clip=clip, alpha=False)
        pix.save(str(dest))
        return dest
    y1 = page.rect.y1 - 28
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
    pixes = [page.get_pixmap(matrix=scale, clip=clip, alpha=False)]
    cont = spec.get("continuation")
    if cont:
        nxt = doc[cont["page"] - 1]
        cut = cont.get("cut_y")
        if cut is None:
            cut = nxt.rect.y0 + 220
        band = pymupdf.Rect(
            nxt.rect.x0, nxt.rect.y0 + 40, nxt.rect.x1, max(nxt.rect.y0 + 56, cut - 4)
        )
        if band.y1 - band.y0 >= 16:
            pixes.append(nxt.get_pixmap(matrix=scale, clip=band, alpha=False))
            return stitch(pixes, dest)
    pixes[0].save(str(dest))
    return dest


def render_chapter_crops(pdf: Path, chapter: dict, dest_dir: Path, prefix: str) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    paths = []
    for spec in chapter.get("crop_plan") or crop_plan(chapter):
        dest = dest_dir / f"{prefix}_q{spec['q_no']:02d}.png"
        render_crop(doc, spec, dest)
        paths.append(dest)
    doc.close()
    return paths


def slug_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def is_answer_key_heading(text: str) -> bool:
    lines = nonempty_lines(text)
    if not lines:
        return False
    return bool(ANSWER_KEY_HEAD.fullmatch(lines[0]))


def find_session_key_page(doc) -> int | None:
    for i in range(doc.page_count):
        if is_answer_key_heading(page_text(doc[i])):
            return i + 1
    return None


def find_answers_solutions_page(doc) -> int | None:
    for i in range(doc.page_count):
        for line in nonempty_lines(page_text(doc[i])):
            if ANSWERS_SOLUTIONS_HEAD.fullmatch(line):
                return i + 1
    return None


def _page_lines(page) -> list[dict]:
    recs = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            txt = "".join(s.get("text") or "" for s in line.get("spans") or []).strip()
            if not txt:
                continue
            x0, y0, x1, y1 = line["bbox"]
            recs.append({"text": txt, "x0": x0, "y0": y0, "y1": y1, "page": page.number + 1})
    return recs


def parse_compact_answer_keys(page) -> tuple[dict[int, str], float]:
    """Return `{q_no: printed_key}` and the bottom y of the compact strip."""
    keys: dict[int, str] = {}
    bottom = page.rect.y0
    for rec in sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"])):
        m = COMPACT_KEY_LINE.fullmatch(rec["text"])
        if not m:
            continue
        q_no = int(m.group(1))
        if q_no in keys:
            continue
        keys[q_no] = m.group(2).strip()
        bottom = max(bottom, float(rec["y1"]))
    return keys, bottom


def solution_anchors(doc, start_page: int, after_y: float, keys: dict | None = None) -> list[dict]:
    """Numbered `n. (key)` write-up headings after the compact key strip.

    Some booklets put the key on the next line (`2.` then `(1)`), so a same-line
    match misses that question.
    """
    anchors = []
    seen: set[int] = set()
    bare = re.compile(r"^(\d{1,2})\.\s*$")
    key_only = re.compile(r"^\(\s*([^)]+?)\s*\)")
    for i in range(start_page - 1, doc.page_count):
        page = doc[i]
        lines = sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"]))
        for idx, rec in enumerate(lines):
            if i == start_page - 1 and rec["y0"] <= after_y + 8:
                continue
            text = rec["text"].replace("\xa0", " ").strip()
            m = SOL_HEAD_LINE.match(text)
            q_no = None
            printed_key = None
            if m:
                q_no = int(m.group(1))
                printed_key = m.group(2).strip()
            else:
                bare_m = bare.match(text)
                if not bare_m:
                    continue
                q_no = int(bare_m.group(1))
                for nxt in lines[idx + 1:]:
                    if nxt["y0"] > rec["y0"] + 28:
                        break
                    km = key_only.match(nxt["text"].replace("\xa0", " ").strip())
                    if km:
                        printed_key = km.group(1).strip()
                        break
                if not printed_key and keys:
                    printed_key = str(keys.get(q_no) or keys.get(str(q_no)) or "").strip()
                    if rec["x0"] > 90:
                        printed_key = ""
                if not printed_key:
                    continue
            if q_no in seen:
                continue
            seen.add(q_no)
            anchors.append({
                "page": i + 1,
                "q_no": q_no,
                "y0": rec["y0"],
                "y1": rec["y1"],
                "heading": rec["text"],
                "printed_key": printed_key,
            })
    return anchors


def question_heading_anchors(doc, end_page: int) -> list[dict]:
    questions = []
    for i in range(end_page - 1):
        page = doc[i]
        for a in session_q_anchors(page):
            questions.append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
            })
        for rec in _page_lines(page):
            m = Q_LINE.match(rec["text"])
            if not m:
                continue
            q_no = int(m.group(1))
            if any(q["q_no"] == q_no for q in questions):
                continue
            questions.append({
                "page": i + 1,
                "q_no": q_no,
                "y0": rec["y0"],
                "y1": rec["y1"],
                "heading": rec["text"],
            })
    questions.sort(key=lambda q: (q["page"], q["y0"], q["q_no"]))
    return questions


def normalize_printed_key(raw: str) -> str:
    return re.sub(r"[()]", "", str(raw or "")).strip()


def inventory_session_solutions_pdf(pdf: Path) -> dict:
    """Session booklet whose keys sit on an 'Answers and Solutions' page.

    Gate: printed Q headings == compact keys == stitched solution crops.
    """
    doc = pymupdf.open(pdf)
    answers_page = find_answers_solutions_page(doc)
    if answers_page is None:
        doc.close()
        return {
            "pdf": str(pdf),
            "style": "printed-solutions",
            "key_page": None,
            "key_pages": [],
            "questions_end_page": None,
            "chapters": [{
                "title": "Definite Integration",
                "pages": [],
                "questions": [],
                "printed": [],
                "printed_count": 0,
                "keys": {},
                "key_count": 0,
                "solutions": [],
                "solution_count": 0,
                "crop_plan": [],
                "crop_count": 0,
                "gate_ok": False,
            }],
            "printed_total": 0,
            "key_total": 0,
            "solution_total": 0,
            "crop_total": 0,
            "gate_ok": False,
        }
    keys, compact_bottom = parse_compact_answer_keys(doc[answers_page - 1])
    printed_qs = question_heading_anchors(doc, answers_page)
    sol_anchors = solution_anchors(doc, answers_page, compact_bottom, keys)
    sol_pages = list(range(answers_page, doc.page_count + 1))
    rec = {
        "title": "Definite Integration",
        "pages": sol_pages,
        "questions": sol_anchors,
        "keys": keys,
    }
    plan = crop_plan(rec)
    printed_nos = sorted({q["q_no"] for q in printed_qs})
    key_nos = sorted(keys)
    sol_nos = sorted({a["q_no"] for a in sol_anchors})
    crop_nos = sorted({s["q_no"] for s in plan})
    gate_ok = (
        printed_nos == key_nos == sol_nos == crop_nos
        and len(printed_nos) > 0
        and len(plan) == len(printed_nos)
    )
    chapter = {
        "title": "Definite Integration",
        "pages": sol_pages,
        "question_pages": list(range(1, answers_page)),
        "questions": sol_anchors,
        "printed_questions": printed_qs,
        "printed": printed_nos,
        "printed_count": len(printed_nos),
        "keys": keys,
        "key_count": len(keys),
        "solutions": sol_nos,
        "solution_count": len(sol_nos),
        "compact_bottom": compact_bottom,
        "crop_plan": plan,
        "crop_count": len(plan),
        "gate_ok": gate_ok,
    }
    doc.close()
    return {
        "pdf": str(pdf),
        "style": "printed-solutions",
        "key_page": answers_page,
        "key_pages": [answers_page],
        "questions_end_page": answers_page,
        "chapters": [chapter],
        "printed_total": chapter["printed_count"],
        "key_total": chapter["key_count"],
        "solution_total": chapter["solution_count"],
        "crop_total": chapter["crop_count"],
        "gate_ok": gate_ok,
    }


def parse_session_keys(text: str) -> dict[int, str]:
    keys: dict[int, str] = {}
    qn = list(SESSION_KEY.finditer(text))
    if qn:
        for m in qn:
            keys[int(m.group(1))] = m.group(2).strip()
        return keys
    for m in KEY_ITEM.finditer(text):
        keys[int(m.group(1))] = m.group(2).strip()
    return keys


def session_q_anchors(page) -> list[dict]:
    """Session booklets: `Q1 - date`, `Q1: date`, or a lone `1.` heading."""
    anchors = []
    width = page.rect.width
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            txt = "".join(s.get("text") or "" for s in line.get("spans") or []).strip()
            m = SESSION_Q.match(txt) or NUM_Q_LINE.match(txt)
            if not m:
                continue
            # "15. 08" is a decimal, not question 15.
            if NUM_Q_LINE.match(txt) and re.match(r"^\d", txt[m.end() :].strip()):
                continue
            x0, y0, _x1, y1 = line["bbox"]
            if x0 > width * 0.72:
                continue
            anchors.append({
                "q_no": int(m.group(1)),
                "y0": y0,
                "y1": y1,
                "heading": txt,
            })
    anchors.sort(key=lambda a: (a["y0"], a["q_no"]))
    dedup = []
    seen = set()
    for a in anchors:
        if a["q_no"] in seen:
            continue
        seen.add(a["q_no"])
        dedup.append(a)
    return dedup


def inventory_session_pdf(pdf: Path) -> dict:
    """Single-chapter MathonGo session booklet: questions until Answer Key, no solutions."""
    doc = pymupdf.open(pdf)
    key_page = find_session_key_page(doc)
    if not key_page:
        doc.close()
        return {
            "pdf": str(pdf),
            "style": "session",
            "key_page": None,
            "key_pages": [],
            "questions_end_page": None,
            "chapters": [{
                "title": "Definite Integration",
                "pages": [],
                "questions": [],
                "printed": [],
                "printed_count": 0,
                "keys": {},
                "key_count": 0,
                "crop_plan": [],
                "crop_count": 0,
                "gate_ok": False,
            }],
            "printed_total": 0,
            "key_total": 0,
            "crop_total": 0,
            "gate_ok": False,
        }
    key_text = page_text(doc[key_page - 1])
    keys = parse_session_keys(key_text)
    questions = []
    pages = list(range(1, key_page))
    for i in range(key_page - 1):
        page = doc[i]
        for a in session_q_anchors(page):
            questions.append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
            })
    rec = {
        "title": "Definite Integration",
        "pages": pages,
        "questions": questions,
        "keys": keys,
    }
    printed = sorted({q["q_no"] for q in questions})
    plan = crop_plan(rec)
    gate_ok = printed == sorted(keys) and len(printed) > 0 and len(plan) == len(printed)
    chapter = {
        "title": "Definite Integration",
        "pages": pages,
        "questions": questions,
        "printed": printed,
        "printed_count": len(printed),
        "keys": keys,
        "key_count": len(keys),
        "crop_plan": plan,
        "crop_count": len(plan),
        "gate_ok": gate_ok,
    }
    doc.close()
    return {
        "pdf": str(pdf),
        "style": "session",
        "key_page": key_page,
        "key_pages": [key_page],
        "questions_end_page": key_page,
        "chapters": [chapter],
        "printed_total": chapter["printed_count"],
        "key_total": chapter["key_count"],
        "crop_total": chapter["crop_count"],
        "gate_ok": gate_ok,
    }


def inventory_session_questionbank_solutions(pdf: Path) -> dict:
    """Question bank with an Answer Key page, then `Q1` / `Q2` write-ups.

    2024 January / April DI booklets use this layout — not `Answers and Solutions`
    and not `1. (key)` headings.
    """
    base = inventory_session_pdf(pdf)
    empty = {
        "pdf": str(pdf),
        "style": "questionbank-solutions",
        "key_page": base.get("key_page"),
        "key_pages": base.get("key_pages") or [],
        "questions_end_page": base.get("questions_end_page"),
        "chapters": [{
            "title": "Definite Integration",
            "pages": [],
            "questions": [],
            "printed": [],
            "printed_count": 0,
            "keys": {},
            "key_count": 0,
            "solutions": [],
            "solution_count": 0,
            "crop_plan": [],
            "crop_count": 0,
            "gate_ok": False,
        }],
        "printed_total": 0,
        "key_total": 0,
        "solution_total": 0,
        "crop_total": 0,
        "gate_ok": False,
    }
    if not base.get("gate_ok") or not base.get("key_page"):
        return empty
    key_page = int(base["key_page"])
    keys = dict(base["chapters"][0]["keys"])
    printed_nos = list(base["chapters"][0]["printed"])
    doc = pymupdf.open(pdf)
    sol_anchors = []
    seen: set[int] = set()
    for i in range(key_page, doc.page_count):
        for a in session_q_anchors(doc[i]):
            q_no = int(a["q_no"])
            if q_no in seen:
                continue
            seen.add(q_no)
            sol_anchors.append({
                "page": i + 1,
                "q_no": q_no,
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
            })
    sol_pages = list(range(key_page + 1, doc.page_count + 1))
    rec = {
        "title": "Definite Integration",
        "pages": sol_pages,
        "questions": sol_anchors,
        "keys": keys,
    }
    plan = crop_plan(rec)
    sol_nos = sorted({a["q_no"] for a in sol_anchors})
    crop_nos = sorted({s["q_no"] for s in plan})
    gate_ok = (
        printed_nos == sorted(keys) == sol_nos == crop_nos
        and len(printed_nos) > 0
        and len(plan) == len(printed_nos)
    )
    chapter = {
        "title": "Definite Integration",
        "pages": sol_pages,
        "question_pages": list(range(1, key_page)),
        "questions": sol_anchors,
        "printed": printed_nos,
        "printed_count": len(printed_nos),
        "keys": keys,
        "key_count": len(keys),
        "solutions": sol_nos,
        "solution_count": len(sol_nos),
        "crop_plan": plan,
        "crop_count": len(plan),
        "gate_ok": gate_ok,
    }
    doc.close()
    return {
        "pdf": str(pdf),
        "style": "questionbank-solutions",
        "key_page": key_page,
        "key_pages": [key_page],
        "questions_end_page": key_page,
        "chapters": [chapter],
        "printed_total": chapter["printed_count"],
        "key_total": chapter["key_count"],
        "solution_total": chapter["solution_count"],
        "crop_total": chapter["crop_count"],
        "gate_ok": gate_ok,
    }


def solution_q_anchors(page) -> list[dict]:
    """`Q11.` then `(3)` under it — 2025 chapter-wise solution write-ups."""
    recs = sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"]))
    width = page.rect.width
    anchors = []
    seen: set[int] = set()
    for rec in recs:
        m = SOL_Q_HEAD.match(rec["text"].replace("\xa0", " ").strip())
        if not m:
            continue
        if rec["x0"] > width * 0.55:
            continue
        q_no = int(m.group(1))
        if q_no in seen:
            continue
        key = (m.group(2) or "").strip() or None
        if key is None:
            for nxt in recs:
                if nxt["y0"] < rec["y0"] - 1:
                    continue
                if nxt["y0"] > rec["y0"] + 45:
                    break
                if abs(float(nxt["x0"]) - float(rec["x0"])) > 14:
                    continue
                km = SOL_KEY_NEAR.match(nxt["text"].replace("\xa0", " ").strip())
                if km:
                    key = km.group(1).strip()
                    break
        seen.add(q_no)
        anchors.append({
            "q_no": q_no,
            "y0": rec["y0"],
            "y1": rec["y1"],
            "heading": rec["text"],
            "printed_key": key,
        })
    return anchors


def inventory_chapterwise_solutions(
    pdf: Path,
    titles: list[str],
    solutions_after: int | None = None,
) -> dict:
    """Worked write-ups in a 2025 Jan/Apr chapter-wise bank (after Answer Keys).

    Gate: compact keys == solution `Qn.` headings == stitched crops.
    """
    doc = pymupdf.open(pdf)
    key_pages = compact_key_pages(doc)
    key_page = key_pages[0] if key_pages else None
    key_text = concatenated_key_text(doc)
    start = solutions_after or (key_pages[-1] + 1 if key_pages else 1)
    want = [t.strip() for t in titles if t.strip()]
    by_title: dict[str, dict] = {
        title: {"title": title, "pages": [], "questions": [], "keys": {}}
        for title in want
    }
    for i in range(start - 1, doc.page_count):
        page = doc[i]
        title = page_chapter_title(page)
        if title not in by_title:
            continue
        rec = by_title[title]
        rec["pages"].append(i + 1)
        for a in solution_q_anchors(page):
            rec["questions"].append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
                "printed_key": a.get("printed_key"),
            })
    for idx, title in enumerate(MATH_CHAPTER_TITLES):
        if title not in by_title:
            continue
        later = list(MATH_CHAPTER_TITLES[idx + 1:])
        by_title[title]["keys"] = parse_section_keys(key_text, title, later)
    doc.close()

    chapters = []
    for title in want:
        rec = by_title.get(title) or {"title": title, "pages": [], "questions": [], "keys": {}}
        printed = sorted({q["q_no"] for q in rec["questions"]})
        keys = rec["keys"]
        plan = crop_plan(rec)
        heading_keys = {
            int(q["q_no"]): q.get("printed_key")
            for q in rec["questions"]
            if q.get("printed_key")
        }
        gate_ok = printed == sorted(int(k) for k in keys) and len(printed) > 0 and len(plan) == len(printed)
        chapters.append({
            "title": title,
            "pages": rec["pages"],
            "questions": rec["questions"],
            "printed": printed,
            "printed_count": len(printed),
            "keys": keys,
            "key_count": len(keys),
            "heading_keys": heading_keys,
            "crop_plan": plan,
            "crop_count": len(plan),
            "solution_count": len(plan),
            "gate_ok": gate_ok,
        })
    return {
        "pdf": str(pdf),
        "kind": "chapterwise-solutions",
        "key_page": key_page,
        "key_pages": key_pages,
        "solutions_start": start,
        "questions_end_page": start,
        "chapters": chapters,
        "printed_total": sum(c["printed_count"] for c in chapters),
        "key_total": sum(c["key_count"] for c in chapters),
        "crop_total": sum(c["crop_count"] for c in chapters),
        "solution_total": sum(c["crop_count"] for c in chapters),
        "gate_ok": all(c["gate_ok"] for c in chapters) and len(chapters) > 0,
    }


def inventory_any_pdf(pdf: Path, titles: list[str] | None = None) -> dict:
    doc = pymupdf.open(pdf)
    answers = find_answers_solutions_page(doc) is not None
    session = find_session_key_page(doc) is not None
    doc.close()
    if answers:
        return inventory_session_solutions_pdf(pdf)
    if session:
        return inventory_session_pdf(pdf)
    return inventory_pdf(pdf, titles)


def format_report(report: dict) -> str:
    lines = [
        f"{report['pdf']}",
        f"  key_pages={report['key_pages']} questions_end={report['questions_end_page']} "
        f"printed={report['printed_total']} keys={report['key_total']} "
        f"solutions={report.get('solution_total', report['crop_total'])} "
        f"crops={report['crop_total']} gate_ok={report['gate_ok']}",
    ]
    for c in report["chapters"]:
        lines.append(
            f"  {c['title']}: pages={c['pages']} printed={c['printed_count']} "
            f"keys={c['key_count']} solutions={c.get('solution_count', c['crop_count'])} "
            f"crops={c['crop_count']} q={c['printed']} gate_ok={c['gate_ok']}"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument(
        "--titles",
        default="",
        help="Comma-separated printed chapter titles. Empty = every titled chapter with Qs or keys.",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--crop-dir", default="", help="Write one PNG crop per printed Q.")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    titles = [t.strip() for t in args.titles.split(",") if t.strip()] or None
    report = inventory_any_pdf(Path(args.pdf), titles)
    if args.crop_dir:
        crop_dir = Path(args.crop_dir)
        for chapter in report["chapters"]:
            paths = render_chapter_crops(
                Path(args.pdf), chapter, crop_dir, slug_title(chapter["title"])
            )
            chapter["crop_files"] = [str(p) for p in paths]
            chapter["gate_ok"] = chapter["gate_ok"] and len(paths) == chapter["printed_count"]
        report["crop_total"] = sum(c["crop_count"] for c in report["chapters"])
        report["gate_ok"] = all(c["gate_ok"] for c in report["chapters"]) and len(report["chapters"]) > 0
    if args.json:
        slim = dict(report)
        slim["chapters"] = []
        for c in report["chapters"]:
            rec = {k: v for k, v in c.items() if k != "questions"}
            slim["chapters"].append(rec)
        print(json.dumps(slim, ensure_ascii=False, indent=1))
    else:
        print(format_report(report), flush=True)
    return 0 if report["gate_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
