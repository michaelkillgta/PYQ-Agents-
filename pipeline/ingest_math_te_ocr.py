#!/usr/bin/env python3
"""OCR-first Trigonometric Equations onto catalog_slug trigonometric-equations.

Session booklets in Maths/Trigonometric Equations plus 2025 Jan/Apr chapter-wise
books. Questions only — solutions are a later pyq-solutions pass.

    python ingest_math_te_ocr.py
    python ingest_math_te_ocr.py --inventory-only
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
import ingest_math_di_sessions_ocr as sess
import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from pyq_ocr_inventory import (
    COMPACT_KEY_LINE,
    DPI,
    KEY_ITEM,
    crop_plan,
    find_answers_solutions_page,
    find_session_key_page,
    inventory_pdf,
    nonempty_lines,
    page_text,
    parse_session_keys,
    q_anchors,
    render_chapter_crops,
    session_q_anchors,
)

CHAPTER_NO = 26
SUBJECT = "Mathematics"
TITLE = "Trigonometric Equations"
NEXT_TITLE = "Inverse Trigonometric"
MCQ_CHOICES = {"1", "2", "3", "4"}
ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-te")

OCR_SYSTEM = sess.OCR_SYSTEM

# Crop-verified stems when gemma4 JSON truncates (2024 Jan Q6: `\n` in `\mathbb{N}`).
PAPER_BODY_FIXES = {
    ("2024-jan", 6): (
        r"If $2\sin^{3} x + \sin 2x \cos x + 4\sin x - 4 = 0$ has exactly 3 solutions "
        r"in the interval $\left[0, \dfrac{n\pi}{2}\right]$, $n \in \mathbb{N}$, then the roots "
        r"of the equation $x^{2} + nx + (n-3) = 0$ belong to :"
    ),
}

SESSION_BOOKS = [
    {
        "id": "2023-jan",
        "kind": "session",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2023_Jan_Trigonometric_Equations.pdf"),
        "out": ROOT / "2023-jan",
        "year": 2023,
        "month_date": "2023-01-01",
    },
    {
        "id": "2023-apr",
        "kind": "session",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2023_Apr_Trigonometric_Equations.pdf"),
        "out": ROOT / "2023-apr",
        "year": 2023,
        "month_date": "2023-04-01",
    },
    {
        "id": "2024-jan",
        "kind": "session",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2024_Jan_Trigonometric_Equations.pdf"),
        "out": ROOT / "2024-jan",
        "year": 2024,
        "month_date": "2024-01-01",
    },
    {
        "id": "2024-apr",
        "kind": "session",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2024_Apr_Trigonometric_Equations.pdf"),
        "out": ROOT / "2024-apr",
        "year": 2024,
        "month_date": "2024-04-01",
    },
    {
        "id": "2026",
        "kind": "session",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2026_Trigonometric_Equations.pdf"),
        "out": ROOT / "2026",
        "year": 2026,
        "month_date": "2026-01-01",
    },
]

CHAPTERWISE_BOOKS = [
    {
        "id": "2025-jan",
        "kind": "chapterwise",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "out": ROOT / "2025-jan",
        "year": 2025,
        "month_date": "2025-01-01",
    },
    {
        "id": "2025-apr",
        "kind": "chapterwise",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "out": ROOT / "2025-apr",
        "year": 2025,
        "month_date": "2025-04-01",
    },
]

BOOKS = SESSION_BOOKS + CHAPTERWISE_BOOKS
BOOK_ORDER = ("2026", "2025-apr", "2025-jan", "2024-apr", "2024-jan", "2023-apr", "2023-jan")


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def parse_te_keys(text: str) -> dict[int, str]:
    keys: dict[int, str] = {}
    for line in nonempty_lines(text):
        m = COMPACT_KEY_LINE.fullmatch(line)
        if m:
            keys[int(m.group(1))] = m.group(2).strip().strip("()")
    if keys:
        return keys
    packed = parse_session_keys(text)
    if packed:
        return packed
    for m in KEY_ITEM.finditer(text):
        keys[int(m.group(1))] = m.group(2).strip()
    return keys


def question_anchors(page) -> list[dict]:
    found: dict[int, dict] = {}
    for a in session_q_anchors(page):
        found[a["q_no"]] = a
    for a in q_anchors(page):
        prev = found.get(a["q_no"]) or {}
        found[a["q_no"]] = {
            "q_no": a["q_no"],
            "y0": a["y0"],
            "y1": a["y1"],
            "heading": prev.get("heading") or "",
        }
    return sorted(found.values(), key=lambda a: (a["y0"], a["q_no"]))


def inventory_session_questions(pdf: Path) -> dict:
    """Questions half only. Never crop the Answers and Solutions write-ups."""
    doc = pymupdf.open(pdf)
    key_page = find_session_key_page(doc) or find_answers_solutions_page(doc)
    if not key_page:
        doc.close()
        return {
            "pdf": str(pdf),
            "style": "session",
            "key_page": None,
            "key_pages": [],
            "questions_end_page": None,
            "chapters": [{
                "title": TITLE, "pages": [], "questions": [], "printed": [],
                "printed_count": 0, "keys": {}, "key_count": 0,
                "crop_plan": [], "crop_count": 0, "gate_ok": False,
            }],
            "printed_total": 0, "key_total": 0, "crop_total": 0, "gate_ok": False,
        }
    keys = parse_te_keys(page_text(doc[key_page - 1]))
    questions = []
    pages = list(range(1, key_page))
    for i in range(key_page - 1):
        page = doc[i]
        for a in question_anchors(page):
            questions.append({
                "page": i + 1,
                "q_no": a["q_no"],
                "y0": a["y0"],
                "y1": a["y1"],
                "heading": a.get("heading") or "",
            })
    rec = {"title": TITLE, "pages": pages, "questions": questions, "keys": keys}
    printed = sorted({q["q_no"] for q in questions})
    plan = crop_plan(rec)
    gate_ok = printed == sorted(keys) and len(printed) > 0 and len(plan) == len(printed)
    chapter = {
        "title": TITLE,
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


def crop_session_key(book: dict, key_page: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[key_page - 1]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def crop_chapterwise_key(book: dict, key_pages: list[int], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    scale = pymupdf.Matrix(DPI / 72, DPI / 72)
    for pno in key_pages:
        page = doc[pno - 1]
        hits = page.search_for(TITLE)
        if not hits:
            continue
        start = min(hits, key=lambda r: r.y0)
        nxt = page.search_for(NEXT_TITLE)
        y1 = min(h.y0 for h in nxt) if nxt else min(page.rect.y1, start.y0 + 90)
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


def inventory_book(book: dict) -> dict:
    if book["kind"] == "chapterwise":
        inv = inventory_pdf(book["pdf"], [TITLE])
    else:
        inv = inventory_session_questions(book["pdf"])
    chapter = inv["chapters"][0]
    report = {
        "id": book["id"],
        "kind": book["kind"],
        "year": book["year"],
        "month_date": book["month_date"],
        "pdf": str(book["pdf"]),
        "out": str(book["out"]),
        "key_page": inv["key_page"],
        "key_pages": inv.get("key_pages") or ([inv["key_page"]] if inv["key_page"] else []),
        "pages": chapter["pages"],
        "questions": chapter["questions"],
        "printed": chapter["printed"],
        "printed_count": chapter["printed_count"],
        "keys": chapter["keys"],
        "key_count": chapter["key_count"],
        "crop_plan": chapter["crop_plan"],
        "crop_count": chapter["crop_count"],
        "gate_ok": bool(inv["gate_ok"] and chapter.get("gate_ok")),
        "chapter": chapter,
    }
    out = book["out"]
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "inventory.json", {
        k: v for k, v in report.items() if k not in ("questions", "crop_plan", "chapter")
    })
    dump(out / "answer_key.json", chapter["keys"])
    return report


def build_jobs(reports: list[dict]) -> list[dict]:
    books = {b["id"]: b for b in BOOKS}
    jobs = []
    for report in reports:
        book = books[report["id"]]
        out = book["out"]
        (out / "crops").mkdir(parents=True, exist_ok=True)
        (out / "ocr").mkdir(parents=True, exist_ok=True)
        (out / "parsed").mkdir(parents=True, exist_ok=True)
        if book["kind"] == "chapterwise":
            key_png = crop_chapterwise_key(
                book, report["key_pages"], out / "crops" / "answer_key.png"
            )
        else:
            key_png = crop_session_key(
                book, report["key_page"], out / "crops" / "answer_key.png"
            )
        render_chapter_crops(book["pdf"], report["chapter"], out / "crops", "q")
        by_q = {spec["q_no"]: spec for spec in report["chapter"]["crop_plan"]}
        headings = {q["q_no"]: q.get("heading") or "" for q in report["questions"]}
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
            })
    return jobs


def ocr_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = job["cache"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        body = PAPER_BODY_FIXES.get((job["booklet"], job["q_no"]))
        if body:
            data = dict(data)
            data["body"] = body
        data["_cached"] = True
        return data
    assert_model_may_see_image(VISION_MODEL)
    prompt = (
        f"Transcribe ONLY PDF Q{job['q_no']} from image 1. "
        f"Official key for Q{job['q_no']} is ({job['raw_key']}). "
        "Keep every printed detail. Do not solve."
    )
    messages = [{"role": "system", "content": OCR_SYSTEM}]
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
    db = ensure_rows(sb, chapter_id, jobs, db)
    live = 0
    holds = []
    for item in results:
        job = item["job"]
        key = (job["booklet"], job["q_no"])
        row = db["by_bbox"].get(key)
        if row is None:
            holds.append({"key": list(key), "reason": "no-db-row"})
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
            if sess.numeric_mcq_options(entry["options"]):
                audit_ok = audit_ok
            else:
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
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    print(f"inventory {len(BOOKS)} Trigonometric Equations PDFs in parallel", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, len(BOOKS))) as pool:
        reports = list(pool.map(inventory_book, BOOKS))
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
    with ThreadPoolExecutor(max_workers=max(1, len(BOOKS))) as pool:
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
            data = json.loads(job["cache"].read_text(encoding="utf-8"))
            body = PAPER_BODY_FIXES.get((job["booklet"], job["q_no"]))
            if body:
                data = dict(data)
                data["body"] = body
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
    dump(ROOT / "publish.json", summary)
    print(f"published live={summary['live']} holds={len(summary['holds'])} (no solutions)", flush=True)
    return 0 if not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
