#!/usr/bin/env python3
"""OCR-first Definite Integration from 2021–2024 MathonGo session PDFs.

Inventory printed Qs vs Answer Key, crop (no solutions pages), gemma4 in one
parallel wave. Do not call glm for worked solutions.

    python ingest_math_di_sessions_ocr.py
    python ingest_math_di_sessions_ocr.py --inventory-only
    python ingest_math_di_sessions_ocr.py --ocr-only
    python ingest_math_di_sessions_ocr.py --publish-only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

import ingest_math_2025_di_ocr as di
import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import VISION_MODEL
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from pyq_ocr_inventory import (
    DPI,
    inventory_session_pdf,
    render_chapter_crops,
)

CHAPTER_NO = 17
SUBJECT = "Mathematics"
MCQ_CHOICES = {"1", "2", "3", "4"}
FROZEN_YEARS = {"2025", "2026"}

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}

HEAD_YMD = re.compile(
    r"Q\s*\d+\s*[-–]\s*20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s*([12])\)",
    re.I,
)
HEAD_DM = re.compile(
    r"Q\s*\d+\s*[-–:]\s*(\d{1,2})\s+([A-Za-z]+)\s*[-–]?\s*\(?Shift\s*([12])\)?",
    re.I,
)
HEAD_BRACKET = re.compile(
    r"\[20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s*([12])\)\]",
    re.I,
)

OCR_SYSTEM = """You look at one printed JEE Main PYQ packet: image 1 is the question crop (full width, both columns), image 2 is that Q's official answer-key strip.
Return JSON only:
{"pdf_q_no":int,"exam_date":"YYYY-MM-DD"|null,"exam_shift":"morning"|"evening"|null,"format":"mcq"|"numerical","body":str,"options":[str,str,str,str]|[],"correct_option":"1"|"2"|"3"|"4"|null,"numerical_answer":str|null}
Transcribe the printed stem and options exactly. Keep every bound, modulus, GIF [x], remainder, and formula. Use $...$ KaTeX for math.
JSON strings must double every TeX backslash: \\int \\frac \\sqrt \\text \\to \\infty \\sin \\cos \\pi \\log. Never write int_ or \\\\int.
Two radicals with + between them are $\\sqrt{A}+\\sqrt{B}$, never nested as $\\sqrt{A+\\sqrt{B}}$ unless one printed bar covers both.
A printed superscript is ^{n}, never \\cdot n. Write $\\sin^{n} x$ when the power sits on sine.
Put the inside of a radical under it: $\\sqrt{\\log_e 9}$, never a power on \\sqrt.
Domain arrows are $(0,\\infty)\\to R$ with \\to and \\infty, never unicode ∫ → ∞ or smashed text.
Paper-only: no solver talk, no book title, no MathonGo, no page numbers, no hints, no worked solution.
If the crop has a printed day and shift, copy them. If it only names a month/year, set exam_date and exam_shift to null.
Copy the official key from image 2 (and the prompt). Do not solve. Do not invent a question."""

# Paper-verified stems (MathonGo session crops). OCR nested a radical, read a
# superscript as \\cdot, smashed \\text/\\to/\\sqrt, wrote \\\\int/\\\\lim,
# dropped GIF powers / Max underscripts / left-hand limits, and unpaired $.
PAPER_BODY_FIXES = {
    ("2022-jun", 2): (
        r"Let $\operatorname{Max}_{0 \le x \le 2} \left\{\dfrac{9-x^{2}}{5-x}\right\} = \alpha$ "
        r"and $\operatorname{Min}_{0 \le x \le 2} \left\{\dfrac{9-x^{2}}{5-x}\right\} = \beta$. "
        r"If $\int_{\beta-\frac{8}{3}}^{2\alpha-1} \operatorname{Max} \left\{\dfrac{9-x^{2}}{5-x}, x\right\} dx "
        r"= \alpha_{1} + \alpha_{2} \log_{e}\left(\dfrac{8}{15}\right)$, then $\alpha_{1} + \alpha_{2}$ is equal to ______"
    ),
    ("2022-jun", 4): (
        r"$\lim_{n \to \infty} \left( \dfrac{n^{2}}{(n^{2}+1)(n+1)} + \dfrac{n^{2}}{(n^{2}+4)(n+2)} "
        r"+ \dfrac{n^{2}}{(n^{2}+9)(n+3)} + \cdots + \dfrac{n^{2}}{(n^{2}+n^{2})(n+n)} \right)$ is equal to"
    ),
    ("2022-jun", 6): (
        r"Let $g : (0, \infty) \to R$ be a differentiable function such that "
        r"$\int \left( \dfrac{x(\cos x - \sin x)}{e^{x}+1} + \dfrac{g(x)(e^{x}+1-xe^{x})}{(e^{x}+1)^{2}} \right) dx "
        r"= \dfrac{xg(x)}{e^{x}+1} + c$, for all $x > 0$, where $c$ is an arbitrary constant. Then,"
    ),
    ("2022-jun", 13): (
        r"Let $f$ be a differentiable function in $\left(0, \dfrac{\pi}{2}\right)$. "
        r"If $\int_{\cos x}^{1} t^{2} f(t)\,dt = \sin^{3} x + \cos x$, then "
        r"$\dfrac{1}{\sqrt{3}} f'\left(\dfrac{1}{\sqrt{3}}\right)$ is equal to :"
    ),
    ("2022-jun", 14): (
        r"The integral $\int_{0}^{1} \dfrac{1}{7^{[1/x]}} dx$, where $[.]$ denotes the greatest integer function is equal to"
    ),
    ("2022-jun", 15): (
        r"Let $[t]$ denote the greatest integer less than or equal to $t$. Then, the value of the integral "
        r"$\int_{0}^{1} \lbrack -8x^{2} + 6x - 1 \rbrack \, dx$ is equal to"
    ),
    ("2022-jun", 16): (
        r"Let $f : \mathbb{R} \to \mathbb{R}$ be a differentiable function such that "
        r"$f\left(\dfrac{\pi}{4}\right) = \sqrt{2}$, $f\left(\dfrac{\pi}{2}\right) = 0$ and "
        r"$f'\left(\dfrac{\pi}{2}\right) = 1$."
        "\n"
        r"Let $g(x) = \int_{x}^{\pi/4} \left(f'(t)\sec t + \tan t \sec t f(t)\right) dt$ "
        r"for $x \in \left[\dfrac{\pi}{4}, \dfrac{\pi}{2}\right)$."
        "\n"
        r"Then $\lim_{x \to \left(\dfrac{\pi}{2}\right)^{-}} g(x)$ is equal to"
    ),
    ("2022-jun", 18): (
        r"$\int_{0}^{5} \cos\left(\pi\left(x - \left[\dfrac{x}{2}\right]\right)\right) dx$, "
        r"where $[t]$ denotes the greatest integer less than or equal to $t$, is equal to :"
    ),
    ("2022-jul", 2): (
        r"$\lim_{n \to \infty} \dfrac{1}{2^{n}} \left( "
        r"\dfrac{1}{\sqrt{1 - \dfrac{1}{2^{n}}}} + \dfrac{1}{\sqrt{1 - \dfrac{2}{2^{n}}}} + "
        r"\dfrac{1}{\sqrt{1 - \dfrac{3}{2^{n}}}} + \cdots + \dfrac{1}{\sqrt{1 - \dfrac{2^{n} - 1}{2^{n}}}} "
        r"\right)$ is equal to"
    ),
    ("2022-jul", 8): (
        r"$\int_{0}^{20\pi} \left(|\sin x| + |\cos x|\right)^{2} \, dx$ is equal to :-"
    ),
    ("2024-jan", 7): (
        r"If $\int_{0}^{1} \frac{1}{\sqrt{3+x}+\sqrt{1+x}} dx = a + b\sqrt{2} + c\sqrt{3}$, "
        r"where $a, b, c$ are rational numbers, then $2a + 3b - 4c$ is equal to :"
    ),
    ("2024-jan", 10): (
        r"If the value of the integral $\int_{-\frac{\pi}{2}}^{\frac{\pi}{2}} \left( "
        r"\frac{x^2 \cos x}{1 + \pi^x} + \frac{1 + \sin^2 x}{1 + e^{\sin^{2033} x}} \right) dx "
        r"= \frac{\pi}{4}(\pi + a) - 2$, then the value of $a$ is"
    ),
    ("2024-jan", 19): (
        r"Let $f, g : (0, \infty) \to R$ be two functions defined by "
        r"$f(x) = \int_{-x}^{x} (|t| - t^2) e^{-t^2} dt$ and "
        r"$g(x) = \int_{0}^{x^2} t^{1/2} e^{-t} dt$. "
        r"Then the value of $\left(f\left(\sqrt{\log_e 9}\right) + g\left(\sqrt{\log_e 9}\right)\right)$ "
        r"is equal to"
    ),
    ("2024-apr", 8): (
        r"$\int_{0}^{\pi/4} \frac{\cos^2 x \sin^2 x}{(\cos^3 x + \sin^3 x)^2} dx$ is equal to"
    ),
}

BOOKS = [
    {
        "id": "2021-feb",
        "pdf": Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_february_chapterwiseW7xhGEpjPf0BnZlSz5TE.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2021-feb"),
        "year": 2021,
        "month_date": "2021-02-01",
    },
    {
        "id": "2021-mar",
        "pdf": Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_march_chapterwise_JhLuivAhhuEbSCISHMto.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2021-mar"),
        "year": 2021,
        "month_date": "2021-03-01",
    },
    {
        "id": "2022-jun",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2022 Chapter wise Questions by MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2022-jun"),
        "year": 2022,
        "month_date": "2022-06-01",
    },
    {
        "id": "2022-jul",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2022-jul"),
        "year": 2022,
        "month_date": "2022-07-01",
    },
    {
        "id": "2023-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 January Chapter wise Questions by MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2023-jan"),
        "year": 2023,
        "month_date": "2023-01-01",
    },
    {
        "id": "2023-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 April Chapterwise PYQ - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2023-apr"),
        "year": 2023,
        "month_date": "2023-04-01",
    },
    {
        "id": "2024-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2024-jan"),
        "year": 2024,
        "month_date": "2024-01-01",
    },
    {
        "id": "2024-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions\2024-apr"),
        "year": 2024,
        "month_date": "2024-04-01",
    },
]


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def apply_paper_body(job: dict, data: dict) -> dict:
    body = PAPER_BODY_FIXES.get((job["booklet"], job["q_no"]))
    if not body:
        return data
    out = dict(data)
    out["body"] = body
    return out


def month_num(token: str) -> int | None:
    key = token.strip().lower()
    if key[:3] in MONTHS:
        return MONTHS[key] if key in MONTHS else MONTHS[key[:3]]
    return MONTHS.get(key)


def shift_of(token: str) -> str:
    return "evening" if str(token).strip() in {"2", "evening"} else "morning"


def parse_heading_meta(heading: str, year: int) -> tuple[str | None, str | None]:
    text = heading or ""
    m = HEAD_YMD.search(text) or HEAD_BRACKET.search(text)
    if m:
        yy = 2000 + int(m.group(1))
        day = int(m.group(2))
        mo = month_num(m.group(3))
        if mo:
            return f"{yy}-{mo:02d}-{day:02d}", shift_of(m.group(4))
    m = HEAD_DM.search(text)
    if m:
        day = int(m.group(1))
        mo = month_num(m.group(2))
        if mo:
            return f"{year}-{mo:02d}-{day:02d}", shift_of(m.group(3))
    return None, None


def inventory_book(book: dict) -> dict:
    inv = inventory_session_pdf(book["pdf"])
    chapter = inv["chapters"][0]
    report = {
        "id": book["id"],
        "year": book["year"],
        "month_date": book["month_date"],
        "pdf": str(book["pdf"]),
        "out": str(book["out"]),
        "key_page": inv["key_page"],
        "pages": chapter["pages"],
        "questions": chapter["questions"],
        "printed": chapter["printed"],
        "printed_count": chapter["printed_count"],
        "keys": chapter["keys"],
        "key_count": chapter["key_count"],
        "crop_plan": chapter["crop_plan"],
        "crop_count": chapter["crop_count"],
        "gate_ok": bool(inv["gate_ok"]),
        "chapter": chapter,
    }
    out = book["out"]
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "inventory.json", {
        k: v for k, v in report.items() if k not in ("questions", "crop_plan", "chapter")
    })
    dump(out / "answer_key.json", chapter["keys"])
    return report


def crop_key_strip(book: dict, key_page: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[key_page - 1]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def build_jobs(reports: list[dict]) -> list[dict]:
    books = {b["id"]: b for b in BOOKS}
    jobs = []
    for report in reports:
        book = books[report["id"]]
        out = book["out"]
        (out / "crops").mkdir(parents=True, exist_ok=True)
        (out / "ocr").mkdir(parents=True, exist_ok=True)
        key_png = crop_key_strip(book, report["key_page"], out / "crops" / "answer_key.png")
        chapter = report["chapter"]
        render_chapter_crops(book["pdf"], chapter, out / "crops", "q")
        by_q = {spec["q_no"]: spec for spec in chapter["crop_plan"]}
        headings = {q["q_no"]: q.get("heading") or "" for q in report["questions"]}
        for q_no in report["printed"]:
            date, shift = parse_heading_meta(headings.get(q_no, ""), book["year"])
            jobs.append({
                "booklet": book["id"],
                "year": book["year"],
                "q_no": q_no,
                "page": by_q[q_no]["page"],
                "heading": headings.get(q_no, ""),
                "crop": out / "crops" / f"q_q{q_no:02d}.png",
                "key_png": key_png,
                "raw_key": report["keys"][q_no],
                "month_date": book["month_date"],
                "heading_date": date,
                "heading_shift": shift,
                "cache": out / "ocr" / f"q_{q_no:02d}.json",
                "out": out,
            })
    return jobs


def ocr_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = job["cache"]
    if cache.exists():
        data = apply_paper_body(job, json.loads(cache.read_text(encoding="utf-8")))
        data["_cached"] = True
        return data
    prompt = (
        f"Transcribe ONLY PDF Q{job['q_no']} from image 1. "
        f"Official key for Q{job['q_no']} is ({job['raw_key']}). "
        "Keep every printed detail. Do not solve."
    )
    messages = [{"role": "system", "content": OCR_SYSTEM}]
    messages.extend(di.two_image_message(job["crop"], job["key_png"], prompt))
    last_err = None
    for _ in range(3):
        try:
            data = apply_paper_body(job, di.v2_json(VISION_MODEL, messages, env, limiter))
            data["_model"] = VISION_MODEL
            dump(cache, data)
            return data
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"{job['booklet']} Q{job['q_no']}: {last_err}")


def run_ocr(jobs: list[dict], env: dict) -> list[dict]:
    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} OCR jobs in parallel | model={VISION_MODEL}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(ocr_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                data = fut.result()
                results.append({"ok": True, "job": job, "data": data})
                tag = "cached" if data.get("_cached") else "ok"
                print(f"  [{tag}] {job['booklet']} Q{job['q_no']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "job": job, "error": str(exc)})
                print(f"  [fail] {job['booklet']} Q{job['q_no']} {exc}", flush=True)
    fails = [r for r in results if not r["ok"]]
    if fails:
        print(f"retry wave {len(fails)}", flush=True)
        with ThreadPoolExecutor(max_workers=max(1, len(fails))) as pool:
            futs = {pool.submit(ocr_one, r["job"], env, limiter): r for r in fails}
            for fut in as_completed(futs):
                prev = futs[fut]
                try:
                    data = fut.result()
                    prev["ok"] = True
                    prev["data"] = data
                    prev.pop("error", None)
                    print(f"  [retry-ok] {prev['job']['booklet']} Q{prev['job']['q_no']}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] {prev['job']['booklet']} Q{prev['job']['q_no']} {exc}", flush=True)
    return results


def pick_exam_date(job: dict, raw: dict) -> tuple[str, str | None]:
    year = str(job["year"])
    date = raw.get("exam_date") if isinstance(raw.get("exam_date"), str) else None
    shift = raw.get("exam_shift") if raw.get("exam_shift") in ("morning", "evening") else None
    if date and date.startswith(year + "-") and re.match(r"\d{4}-\d{2}-\d{2}$", date):
        if date[5:7] == "00" or date[8:10] == "00":
            date = None
        else:
            return date, shift or job.get("heading_shift")
    if job.get("heading_date"):
        return job["heading_date"], job.get("heading_shift")
    return job["month_date"], job.get("heading_shift")


def numeric_mcq_options(options: list | None) -> bool:
    if not isinstance(options, list) or len(options) != 4:
        return False
    return all(re.fullmatch(r"-?\d+", str(o or "").strip()) for o in options)


def clean_entry(raw: dict) -> dict:
    entry = di.clean_entry(raw)
    body_raw = str(raw.get("body") or "").strip()
    if entry.get("body") and not katex_render_ok(entry["body"]) and katex_render_ok(body_raw):
        entry["body"] = body_raw
    raw_opts = raw.get("options")
    if isinstance(raw_opts, list) and isinstance(entry.get("options"), list):
        fixed = []
        for i, o in enumerate(entry["options"]):
            orig = str(raw_opts[i] if i < len(raw_opts) else "")
            if o and not katex_render_ok(o) and katex_render_ok(orig):
                fixed.append(orig)
            else:
                fixed.append(o)
        entry["options"] = fixed
    return entry


def mcq_option(raw: str) -> int | None:
    v = str(raw or "").strip().upper()
    if v in "ABCD":
        return "ABCD".index(v) + 1
    if v in MCQ_CHOICES:
        return int(v)
    return None


def fetch_chapter_rows(sb, chapter_id: int) -> dict:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,exam_date,source_bbox,review_status,format")
        .eq("chapter_id", chapter_id)
        .execute()
        .data
        or []
    )
    by_bbox: dict[tuple[str, int], dict] = {}
    max_q = 0
    for row in rows:
        max_q = max(max_q, int(row["q_no"]))
        bbox = row.get("source_bbox") or {}
        booklet = bbox.get("booklet")
        pdf_q = bbox.get("pdf_q")
        date = str(row.get("exam_date") or "")
        if date[:4] in FROZEN_YEARS:
            continue
        if booklet and pdf_q is not None:
            by_bbox[(str(booklet), int(pdf_q))] = row
    return {"by_bbox": by_bbox, "max_q": max_q, "rows": rows}


def ensure_rows(sb, chapter_id: int, jobs: list[dict], db: dict) -> dict:
    by_bbox = db["by_bbox"]
    max_q = db["max_q"]
    seed = []
    for job in jobs:
        key = (job["booklet"], job["q_no"])
        if key in by_bbox:
            continue
        raw = job["raw_key"]
        choice = mcq_option(raw)
        kind = "mcq" if choice is not None else "numerical"
        max_q += 1
        seed.append({
            "chapter_id": chapter_id,
            "topic_id": None,
            "q_no": max_q,
            "tier": "must_do",
            "format": kind,
            "body": None,
            "correct_option": choice if kind == "mcq" else None,
            "numerical_answer": None if kind == "mcq" else str(raw),
            "exam_date": job.get("heading_date") or job["month_date"],
            "exam_shift": job.get("heading_shift"),
            "out_of_syllabus": False,
            "good_to_solve": False,
            "source_page": job["page"],
            "source_bbox": {"booklet": job["booklet"], "pdf_q": job["q_no"]},
            "review_status": "skeleton_only",
        })
        print(f"  insert {job['booklet']} Q{job['q_no']} as q_no {max_q}", flush=True)
    if seed:
        sb.table("pyq_questions").insert(seed).execute()
        return fetch_chapter_rows(sb, chapter_id)
    return db


def publish_results(sb, chapter_id: int, results: list[dict]) -> dict:
    db = fetch_chapter_rows(sb, chapter_id)
    jobs = [item["job"] for item in results]
    jobs.sort(key=lambda j: (j["booklet"], j["q_no"]))
    db = ensure_rows(sb, chapter_id, jobs, db)
    live = 0
    holds = []
    for item in results:
        job = item["job"]
        key = (job["booklet"], job["q_no"])
        row = db["by_bbox"].get(key)
        if row is None:
            holds.append({"key": key, "reason": "no-db-row"})
            continue
        date_existing = str(row.get("exam_date") or "")
        if date_existing[:4] in FROZEN_YEARS:
            holds.append({"key": key, "reason": "frozen-year"})
            continue
        if not item.get("ok"):
            holds.append({"key": key, "reason": item.get("error")})
            continue
        raw = item["data"]
        entry = clean_entry(raw)
        spec = {
            "q_no": job["q_no"],
            "raw_key": job["raw_key"],
            "answer_type": "mcq",
            "answer_value": job["raw_key"],
        }
        spec = di.refine_type(spec, entry)
        if spec["answer_type"] == "numerical":
            entry["options"] = None
        date, shift = pick_exam_date(job, raw)
        dump(job["out"] / "parsed" / f"q_{job['q_no']:02d}.json", {
            "spec": spec, "entry": entry, "exam_date": date, "exam_shift": shift,
        })
        shape_ok = shape_ok_for(spec, entry)
        audit_ok = not flags_for(entry.get("body") or "", is_option=False)
        if entry.get("options"):
            if numeric_mcq_options(entry["options"]):
                audit_ok = audit_ok
            else:
                audit_ok = audit_ok and all(not flags_for(o or "", is_option=True) for o in entry["options"])
        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        katex_ok = all(katex_render_ok(t) for t in fields)
        solver_dump = is_solver_dump(entry.get("body") or "")
        publishable = shape_ok and audit_ok and katex_ok and not solver_dump and spec.get("answer_value")
        status = "human_ok" if publishable else "unreviewed"
        fmt = spec["answer_type"]
        choice = mcq_option(spec["answer_value"]) if fmt == "mcq" else None
        sb.table("pyq_questions").update({
            "format": fmt,
            "exam_date": date,
            "exam_shift": shift,
            "source_page": job["page"],
            "source_bbox": {"booklet": job["booklet"], "pdf_q": job["q_no"]},
            "correct_option": choice if fmt == "mcq" else None,
            "numerical_answer": None if fmt == "mcq" else str(spec["answer_value"]),
        }).eq("id", row["id"]).execute()
        upsert_question(
            sb, row["id"], entry, status,
            1.0 if status == "human_ok" else 0.5,
            spec,
            answer=str(spec.get("answer_value") or ""),
        )
        if fmt == "numerical":
            sb.table("pyq_question_options").delete().eq("question_id", row["id"]).execute()
        tag = "LIVE" if status == "human_ok" else "HOLD"
        print(f"  [{tag}] {job['booklet']} Q{job['q_no']} db={row['q_no']} {status}", flush=True)
        if status == "human_ok":
            live += 1
        else:
            holds.append({
                "booklet": job["booklet"], "pdf_q": job["q_no"], "db_q": row["q_no"],
                "shape_ok": shape_ok, "audit_ok": audit_ok, "katex_ok": katex_ok,
                "preview": (entry.get("body") or "")[:160],
            })
    return {"live": live, "holds": holds}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    ap.add_argument("--force-ocr", action="store_true")
    ap.add_argument("--books", default="", help="comma booklet ids, default all")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    want = {x.strip() for x in args.books.split(",") if x.strip()}
    books = [b for b in BOOKS if not want or b["id"] in want]
    if not books:
        print(f"no books matched {args.books!r}", flush=True)
        return 2

    print(f"inventory {len(books)} Definite Integration session PDFs in parallel", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, len(books))) as pool:
        reports = list(pool.map(inventory_book, books))
    failed = False
    for r in reports:
        print(
            f"  {r['id']}: pages={r['pages']} printed={r['printed_count']} "
            f"keys={r['key_count']} crops={r['crop_count']} gate_ok={r['gate_ok']}",
            flush=True,
        )
        if not r["gate_ok"]:
            failed = True
            print("STOP: printed Q set does not match the Answer Key.", flush=True)
    if failed:
        return 2
    if args.inventory_only:
        return 0

    print("crop all books in parallel", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, len(books))) as pool:
        jobs_nested = list(pool.map(lambda report: build_jobs([report]), reports))
    jobs = [job for group in jobs_nested for job in group]
    missing = [j for j in jobs if not j["crop"].is_file()]
    if missing:
        print(f"STOP: {len(missing)} crops missing", flush=True)
        return 2
    print(f"cropped {len(jobs)} questions", flush=True)
    if args.force_ocr:
        for job in jobs:
            if job["cache"].exists():
                job["cache"].unlink()

    if args.publish_only:
        results = []
        for job in jobs:
            if not job["cache"].exists():
                print(f"missing OCR cache {job['cache']}", flush=True)
                return 2
            data = apply_paper_body(job, json.loads(job["cache"].read_text(encoding="utf-8")))
            if (job["booklet"], job["q_no"]) in PAPER_BODY_FIXES:
                dump(job["cache"], data)
            results.append({
                "ok": True,
                "job": job,
                "data": data,
            })
    else:
        env = p.load_env()
        results = run_ocr(jobs, env)
        still = [r for r in results if not r.get("ok")]
        if still:
            print(f"OCR holds {len(still)} — not publishing those rows", flush=True)

    if args.ocr_only:
        ok = sum(1 for r in results if r.get("ok"))
        print(f"OCR done {ok}/{len(results)}", flush=True)
        return 0 if ok == len(results) else 2

    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    summary = publish_results(sb, chapter_id, results)
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-di-sessions") / "publish.json", summary)
    print(f"published live={summary['live']} holds={len(summary['holds'])} (no solutions)", flush=True)
    return 0 if not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
