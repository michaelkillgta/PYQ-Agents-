#!/usr/bin/env python3
"""OCR-first Maths session + 2025 chapterwise banks onto named catalog chapters.

Questions only. Solutions are ingest_math_named_solutions.py.

    python ingest_math_named_ocr.py --inventory-only
    python ingest_math_named_ocr.py
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

import ingest_math_2025_di_ocr as di
import ingest_math_di_sessions_ocr as sess
import ingest_math_te_ocr as te
import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from pyq_ocr_inventory import (
    DPI,
    inventory_pdf,
    render_chapter_crops,
)

SUBJECT = "Mathematics"
MATH = Path(r"C:\Users\tempo\Downloads\Maths")
JAN25 = MATH / "Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"
APR25 = MATH / "Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"
FILES = Path(r"c:\Users\tempo\Downloads\files")
BOOK_ORDER = ("2026", "2025-apr", "2025-jan", "2024-apr", "2024-jan", "2023-apr", "2023-jan")
MCQ_CHOICES = {"1", "2", "3", "4"}

# Screenshot ten: DI already live 2020–2026. Skip it here.
CHAPTERS = [
    {"no": 1, "title": "Basic of Mathematics", "next": "Quadratic Equation", "folder": "Basic of Mathematics", "short": "bom", "skip_2025": False},
    {"no": 3, "title": "Complex Number", "next": "Sequences and Series", "folder": "Complex Number", "short": "cn", "skip_2025": False},
    {"no": 6, "title": "Binomial Theorem", "next": "Statistics", "folder": "Binomial Theorem", "short": "bt", "skip_2025": False},
    {"no": 9, "title": "Determinants", "next": "Probability", "folder": "Determinants", "short": "det", "skip_2025": False},
    {"no": 14, "title": "Continuity and Differentiability", "next": "Application of Derivatives", "folder": "Continuity and Differentiability", "short": "cad", "skip_2025": False},
    {"no": 15, "title": "Application of Derivatives", "next": "Indefinite Integration", "folder": "Application of Derivatives", "short": "aod", "skip_2025": False},
    {"no": 18, "title": "Area Under Curves", "next": "Differential Equations", "folder": "Area Under Curves", "short": "auc", "skip_2025": True},
    {"no": 19, "title": "Differential Equations", "next": "Straight Lines", "folder": "Differential Equations", "short": "de", "skip_2025": True},
    {"no": 21, "title": "Circle", "next": "Parabola", "folder": "Circle", "short": "cir", "skip_2025": False},
    {"no": 12, "title": "Functions", "next": "Limits", "folder": "Functions", "short": "fn", "skip_2025": False},
    {"no": 23, "title": "Ellipse", "next": "Hyperbola", "folder": "Ellipse", "short": "ell", "skip_2025": False},
    {"no": 24, "title": "Hyperbola", "next": "Trigonometric Ratios & Identities", "folder": "Hyperbola", "short": "hyp", "skip_2025": False},
    {"no": 13, "title": "Limits", "next": "Continuity and Differentiability", "folder": "Limits", "short": "lim", "skip_2025": False},
    {"no": 16, "title": "Indefinite Integration", "next": "Definite Integration", "folder": "Indefinite Integration", "short": "ii", "skip_2025": False},
    {"no": 27, "title": "Inverse Trigonometric Functions", "next": "Vector Algebra", "folder": "Inverse Trigonometric Functions", "short": "itf", "skip_2025": False},
    {"no": 30, "title": "Differentiation", "next": "Ellipse", "folder": "Differentiation", "short": "diff", "skip_2025": True},
    {"no": 31, "title": "Limits, Continuity and Differentiability", "next": "Matrices", "folder": "Limits, Continuity and Differentiability", "short": "lcd", "skip_2025": True},
    {"no": 8, "title": "Matrices", "next": "Determinants", "folder": "Matrices", "short": "mat", "skip_2025": False},
    {"no": 5, "title": "Permutation Combination", "next": "Binomial Theorem", "folder": "Permutation Combination", "short": "perm", "skip_2025": False},
    {"no": 10, "title": "Probability", "next": "Sets and Relations", "folder": "Probability", "short": "prob", "skip_2025": False},
    {"no": 22, "title": "Parabola", "next": "Ellipse", "folder": "Parabola", "short": "par", "skip_2025": False},
    {"no": 2, "title": "Quadratic Equation", "next": "Complex Number", "folder": "Quadratic Equation", "short": "qe", "skip_2025": False},
    {"no": 4, "title": "Sequences and Series", "next": "Permutation Combination", "folder": "Sequences and Series", "short": "seq", "skip_2025": False},
    {"no": 11, "title": "Sets and Relations", "next": "Functions", "folder": "Sets and Relations", "short": "set", "skip_2025": False},
    {"no": 7, "title": "Statistics", "next": "Matrices", "folder": "Statistics", "short": "stat", "skip_2025": False},
    {"no": 20, "title": "Straight Lines", "next": "Circle", "folder": "Straight Lines", "short": "sl", "skip_2025": False},
]


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def session_pdf(folder: str, stem: str) -> Path | None:
    path = MATH / folder / stem
    return path if path.is_file() else None


def books_for(ch: dict) -> list[dict]:
    folder = ch["folder"]
    root = FILES / f"out-math-{ch['short']}"
    books = []
    sessions = [
        ("2023-jan", f"2023_Jan_{folder.replace(' ', '_')}.pdf", 2023, "2023-01-01"),
        ("2023-apr", f"2023_Apr_{folder.replace(' ', '_')}.pdf", 2023, "2023-04-01"),
        ("2024-jan", f"2024_Jan_{folder.replace(' ', '_')}.pdf", 2024, "2024-01-01"),
        ("2024-apr", f"2024_Apr_{folder.replace(' ', '_')}.pdf", 2024, "2024-04-01"),
        ("2026", f"2026_{folder.replace(' ', '_')}.pdf", 2026, "2026-01-01"),
    ]
    for bid, stem, year, month_date in sessions:
        pdf = session_pdf(folder, stem)
        if pdf is None:
            continue
        books.append({
            "id": bid,
            "kind": "session",
            "pdf": pdf,
            "out": root / bid,
            "year": year,
            "month_date": month_date,
            "title": ch["title"],
            "next": ch["next"],
            "chapter_no": ch["no"],
            "short": ch["short"],
        })
    if not ch["skip_2025"]:
        for bid, pdf, month_date, year in (
            ("2025-jan", JAN25, "2025-01-01", 2025),
            ("2025-apr", APR25, "2025-04-01", 2025),
        ):
            books.append({
                "id": bid,
                "kind": "chapterwise",
                "pdf": pdf,
                "out": root / bid,
                "year": year,
                "month_date": month_date,
                "title": ch["title"],
                "next": ch["next"],
                "chapter_no": ch["no"],
                "short": ch["short"],
            })
    return books


def inventory_session(book: dict) -> dict:
    title = book["title"]
    pdf = book["pdf"]
    doc = pymupdf.open(pdf)
    key_page = te.find_session_key_page(doc) if hasattr(te, "find_session_key_page") else None
    from pyq_ocr_inventory import find_answers_solutions_page, find_session_key_page, page_text, crop_plan

    key_page = find_session_key_page(doc) or find_answers_solutions_page(doc)
    if not key_page:
        doc.close()
        empty = {
            "title": title, "pages": [], "questions": [], "printed": [],
            "printed_count": 0, "keys": {}, "key_count": 0,
            "crop_plan": [], "crop_count": 0, "gate_ok": False,
        }
        return {
            "id": book["id"], "kind": "session", "year": book["year"],
            "month_date": book["month_date"], "pdf": str(pdf), "out": str(book["out"]),
            "key_page": None, "key_pages": [], "pages": [], "questions": [],
            "printed": [], "printed_count": 0, "keys": {}, "key_count": 0,
            "crop_plan": [], "crop_count": 0, "gate_ok": False, "chapter": empty,
            "chapter_no": book["chapter_no"], "short": book["short"], "title": title,
        }
    keys = te.parse_te_keys(page_text(doc[key_page - 1]))
    questions = []
    pages = list(range(1, key_page))
    for i in range(key_page - 1):
        for a in te.question_anchors(doc[i]):
            questions.append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
            })
    rec = {"title": title, "pages": pages, "questions": questions, "keys": keys}
    printed = sorted({q["q_no"] for q in questions})
    plan = crop_plan(rec)
    gate_ok = printed == sorted(keys) and len(printed) > 0 and len(plan) == len(printed)
    chapter = {
        "title": title, "pages": pages, "questions": questions, "printed": printed,
        "printed_count": len(printed), "keys": keys, "key_count": len(keys),
        "crop_plan": plan, "crop_count": len(plan), "gate_ok": gate_ok,
    }
    doc.close()
    report = {
        "id": book["id"], "kind": "session", "year": book["year"],
        "month_date": book["month_date"], "pdf": str(pdf), "out": str(book["out"]),
        "key_page": key_page, "key_pages": [key_page], "pages": pages,
        "questions": questions, "printed": printed, "printed_count": len(printed),
        "keys": keys, "key_count": len(keys), "crop_plan": plan, "crop_count": len(plan),
        "gate_ok": gate_ok, "chapter": chapter, "chapter_no": book["chapter_no"],
        "short": book["short"], "title": title,
    }
    out = book["out"]
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "inventory.json", {k: v for k, v in report.items() if k not in ("questions", "crop_plan", "chapter")})
    dump(out / "answer_key.json", keys)
    return report


def crop_chapterwise_key(book: dict, key_pages: list[int], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    title = book["title"]
    nxt = book["next"]
    doc = pymupdf.open(book["pdf"])
    scale = pymupdf.Matrix(DPI / 72, DPI / 72)
    for pno in key_pages:
        page = doc[pno - 1]
        hits = page.search_for(title)
        if not hits:
            continue
        start = min(hits, key=lambda r: r.y0)
        nxt_hits = page.search_for(nxt)
        y1 = min(h.y0 for h in nxt_hits) if nxt_hits else min(page.rect.y1, start.y0 + 90)
        clip = pymupdf.Rect(page.rect.x0, max(page.rect.y0, start.y0 - 4), page.rect.x1, y1)
        pix = page.get_pixmap(matrix=scale, clip=clip, alpha=False)
        pix.save(str(dest))
        doc.close()
        return dest
    page = doc[key_pages[0] - 1]
    pix = page.get_pixmap(matrix=scale, alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def inventory_chapterwise(book: dict) -> dict:
    inv = inventory_pdf(book["pdf"], [book["title"]])
    chapter = inv["chapters"][0]
    report = {
        "id": book["id"], "kind": "chapterwise", "year": book["year"],
        "month_date": book["month_date"], "pdf": str(book["pdf"]), "out": str(book["out"]),
        "key_page": inv["key_page"],
        "key_pages": inv.get("key_pages") or ([inv["key_page"]] if inv["key_page"] else []),
        "pages": chapter["pages"], "questions": chapter["questions"],
        "printed": chapter["printed"], "printed_count": chapter["printed_count"],
        "keys": chapter["keys"], "key_count": chapter["key_count"],
        "crop_plan": chapter["crop_plan"], "crop_count": chapter["crop_count"],
        "gate_ok": bool(inv["gate_ok"] and chapter.get("gate_ok")),
        "chapter": chapter, "chapter_no": book["chapter_no"],
        "short": book["short"], "title": book["title"],
    }
    out = book["out"]
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "inventory.json", {k: v for k, v in report.items() if k not in ("questions", "crop_plan", "chapter")})
    dump(out / "answer_key.json", chapter["keys"])
    return report


def inventory_book(book: dict) -> dict:
    if book["kind"] == "chapterwise":
        return inventory_chapterwise(book)
    return inventory_session(book)


def build_jobs(book: dict, report: dict) -> list[dict]:
    out = book["out"]
    (out / "crops").mkdir(parents=True, exist_ok=True)
    (out / "ocr").mkdir(parents=True, exist_ok=True)
    (out / "parsed").mkdir(parents=True, exist_ok=True)
    if book["kind"] == "chapterwise":
        key_png = crop_chapterwise_key(book, report["key_pages"], out / "crops" / "answer_key.png")
    else:
        key_png = te.crop_session_key(book, report["key_page"], out / "crops" / "answer_key.png")
    render_chapter_crops(book["pdf"], report["chapter"], out / "crops", "q")
    by_q = {spec["q_no"]: spec for spec in report["chapter"]["crop_plan"]}
    headings = {q["q_no"]: q.get("heading") or "" for q in report["questions"]}
    jobs = []
    for q_no in report["printed"]:
        date, shift = sess.parse_heading_meta(headings.get(q_no, ""), book["year"])
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
            "chapter_no": book["chapter_no"],
            "short": book["short"],
            "title": book["title"],
        })
    return jobs


def ocr_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = job["cache"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["_cached"] = True
        return data
    assert_model_may_see_image(VISION_MODEL)
    prompt = (
        f"Transcribe ONLY PDF Q{job['q_no']} from image 1. "
        f"Official key for Q{job['q_no']} is ({job['raw_key']}). "
        "Keep every printed detail. Do not solve."
    )
    messages = [{"role": "system", "content": sess.OCR_SYSTEM}]
    messages.extend(di.two_image_message(job["crop"], job["key_png"], prompt))
    last_err = None
    for _ in range(5):
        try:
            data = di.v2_json(VISION_MODEL, messages, env, limiter)
            data["_model"] = VISION_MODEL
            dump(cache, data)
            return data
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"{job['short']} {job['booklet']} Q{job['q_no']}: {last_err}")


def run_ocr(jobs: list[dict], env: dict) -> list[dict]:
    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} OCR jobs in parallel | model={VISION_MODEL}", flush=True)
    results = []
    workers = min(32, max(1, len(jobs)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(ocr_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                data = fut.result()
                results.append({"ok": True, "job": job, "data": data})
                tag = "cached" if data.get("_cached") else "ok"
                print(f"  [{tag}] {job['short']} {job['booklet']} Q{job['q_no']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "job": job, "error": str(exc)})
                print(f"  [fail] {job['short']} {job['booklet']} Q{job['q_no']} {exc}", flush=True)
    fails = [r for r in results if not r["ok"]]
    if fails:
        print(f"retry wave {len(fails)}", flush=True)
        with ThreadPoolExecutor(max_workers=min(32, max(1, len(fails)))) as pool:
            futs = {pool.submit(ocr_one, r["job"], env, limiter): r for r in fails}
            for fut in as_completed(futs):
                prev = futs[fut]
                try:
                    data = fut.result()
                    prev["ok"] = True
                    prev["data"] = data
                    prev.pop("error", None)
                    print(f"  [retry-ok] {prev['job']['short']} {prev['job']['booklet']} Q{prev['job']['q_no']}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] {prev['job']['short']} {prev['job']['booklet']} Q{prev['job']['q_no']} {exc}", flush=True)
    return results


def fetch_chapter_rows(sb, chapter_id: int) -> dict:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,exam_date,source_bbox,review_status,format,body")
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
        if booklet and pdf_q is not None:
            by_bbox[(str(booklet), int(pdf_q))] = row
    return {"by_bbox": by_bbox, "max_q": max_q, "rows": rows}


def mcq_option(raw: str) -> int | None:
    v = str(raw or "").strip().upper()
    if v in "ABCD":
        return "ABCD".index(v) + 1
    if v in MCQ_CHOICES:
        return int(v)
    return None


def ensure_rows(sb, chapter_id: int, jobs: list[dict], db: dict) -> dict:
    by_bbox = db["by_bbox"]
    max_q = db["max_q"]
    seed = []
    ordered = sorted(jobs, key=lambda j: (BOOK_ORDER.index(j["booklet"]), j["q_no"]))
    for job in ordered:
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
            "source_bbox": {"booklet": job["booklet"], "pdf_q": job["q_no"], "chapter": job["short"]},
            "review_status": "skeleton_only",
        })
        print(f"  insert {job['short']} {job['booklet']} Q{job['q_no']} as q_no {max_q}", flush=True)
    if seed:
        for i in range(0, len(seed), 20):
            sb.table("pyq_questions").insert(seed[i : i + 20]).execute()
        return fetch_chapter_rows(sb, chapter_id)
    return db


def publish_chapter(sb, chapter_no: int, results: list[dict]) -> dict:
    chapter_id = p.resolve_chapter_id(sb, chapter_no, SUBJECT)
    db = fetch_chapter_rows(sb, chapter_id)
    jobs = [item["job"] for item in results]
    db = ensure_rows(sb, chapter_id, jobs, db)
    live = 0
    holds = []
    skipped = 0
    for item in results:
        job = item["job"]
        key = (job["booklet"], job["q_no"])
        row = db["by_bbox"].get(key)
        if row is None:
            holds.append({"key": list(key), "reason": "no-db-row"})
            continue
        if row.get("review_status") in {"auto_ok", "human_ok"} and (row.get("body") or "").strip():
            skipped += 1
            continue
        if not item.get("ok"):
            holds.append({"key": list(key), "reason": item.get("error")})
            continue
        raw = item["data"]
        entry = sess.clean_entry(raw)
        spec = {
            "q_no": job["q_no"],
            "raw_key": job["raw_key"],
            "answer_type": "mcq",
            "answer_value": job["raw_key"],
        }
        spec = di.refine_type(spec, entry)
        if spec["answer_type"] == "numerical":
            entry["options"] = None
        date, shift = sess.pick_exam_date(job, raw)
        dump(job["out"] / "parsed" / f"q_{job['q_no']:02d}.json", {
            "spec": spec, "entry": entry, "exam_date": date, "exam_shift": shift,
        })
        shape_ok = shape_ok_for(spec, entry)
        audit_ok = not flags_for(entry.get("body") or "", is_option=False)
        if entry.get("options"):
            if not sess.numeric_mcq_options(entry["options"]):
                audit_ok = audit_ok and all(
                    not flags_for(o or "", is_option=True) for o in entry["options"]
                )
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
            "source_bbox": {"booklet": job["booklet"], "pdf_q": job["q_no"], "chapter": job["short"]},
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
        print(f"  [{tag}] {job['short']} {job['booklet']} Q{job['q_no']} db={row['q_no']} {status}", flush=True)
        if status == "human_ok":
            live += 1
        else:
            holds.append({
                "booklet": job["booklet"], "pdf_q": job["q_no"], "db_q": row["q_no"],
                "short": job["short"], "shape_ok": shape_ok, "audit_ok": audit_ok,
                "katex_ok": katex_ok, "preview": (entry.get("body") or "")[:160],
            })
    return {"live": live, "holds": holds, "skipped": skipped, "chapter_no": chapter_no}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    ap.add_argument("--chapters", default="", help="comma chapter_no, empty = screenshot nine minus DI")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    want = CHAPTERS
    if args.chapters.strip():
        nos = {int(x) for x in args.chapters.split(",") if x.strip()}
        want = [c for c in CHAPTERS if c["no"] in nos]

    all_books = []
    for ch in want:
        all_books.extend(books_for(ch))
    print(f"inventory {len(all_books)} PDFs across {len(want)} chapters", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, min(16, len(all_books)))) as pool:
        reports = list(pool.map(inventory_book, all_books))

    failed = False
    kept = []
    for r in reports:
        empty = r["printed_count"] == 0 and r["key_count"] == 0
        print(
            f"  ch{r['chapter_no']} {r['id']}: printed={r['printed_count']} "
            f"keys={r['key_count']} crops={r['crop_count']} gate_ok={r['gate_ok']}"
            + (" skip-empty" if empty else ""),
            flush=True,
        )
        if empty:
            continue
        if not r["gate_ok"]:
            failed = True
        kept.append(r)
    reports = kept
    if failed:
        print("STOP: printed Q set does not match the Answer Key.", flush=True)
        return 2
    if args.inventory_only:
        return 0

    print("crop all books in parallel", flush=True)
    books_by_key = {(b["chapter_no"], b["id"]): b for b in all_books}
    jobs = []
    with ThreadPoolExecutor(max_workers=max(1, min(12, len(reports)))) as pool:
        futs = []
        for report in reports:
            book = books_by_key[(report["chapter_no"], report["id"])]
            futs.append(pool.submit(build_jobs, book, report))
        for fut in futs:
            jobs.extend(fut.result())
    missing = [j for j in jobs if not j["crop"].is_file()]
    if missing:
        print(f"STOP: {len(missing)} crops missing", flush=True)
        return 2
    print(f"cropped {len(jobs)} questions", flush=True)

    if args.publish_only:
        results = []
        for job in jobs:
            if not job["cache"].exists():
                print(f"missing OCR cache {job['cache']}", flush=True)
                return 2
            data = json.loads(job["cache"].read_text(encoding="utf-8"))
            results.append({"ok": True, "job": job, "data": data})
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
    summaries = []
    by_ch: dict[int, list] = {}
    for item in results:
        by_ch.setdefault(item["job"]["chapter_no"], []).append(item)
    for ch in want:
        summary = publish_chapter(sb, ch["no"], by_ch.get(ch["no"], []))
        summaries.append(summary)
        dump(FILES / f"out-math-{ch['short']}" / "publish.json", summary)
        print(
            f"ch{ch['no']} {ch['title']}: live={summary['live']} "
            f"holds={len(summary['holds'])} skipped={summary['skipped']}",
            flush=True,
        )
    dump(FILES / "out-math-named" / "publish.json", summaries)
    holds = sum(len(s["holds"]) for s in summaries)
    return 0 if holds == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
