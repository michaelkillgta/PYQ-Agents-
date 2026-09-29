#!/usr/bin/env python3
"""Paper OCR for Trigonometric Equations worked write-ups. gemma4. Never glm.

2023 January has no printed write-up — glm sheet is a later pass.

    python ingest_math_te_paper_solutions.py
    python ingest_math_te_paper_solutions.py --inventory-only
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

import ingest_math_2025_paper_solutions as paper
import pyq_common as p
from pyq_ocr_inventory import (
    crop_plan,
    find_answers_solutions_page,
    find_session_key_page,
    inventory_chapterwise_solutions,
    inventory_session_questionbank_solutions,
    inventory_session_solutions_pdf,
    parse_compact_answer_keys,
    question_heading_anchors,
    render_crop,
    solution_anchors,
)

CHAPTER_NO = 26
SUBJECT = "Mathematics"
TITLE = "Trigonometric Equations"
ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-te-solutions")

BOOKS = [
    {
        "id": "2023-apr",
        "kind": "keypage",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2023_Apr_Trigonometric_Equations.pdf"),
        "out": ROOT / "2023-apr",
    },
    {
        "id": "2024-jan",
        "kind": "questionbank",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2024_Jan_Trigonometric_Equations.pdf"),
        "out": ROOT / "2024-jan",
    },
    {
        "id": "2024-apr",
        "kind": "questionbank",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2024_Apr_Trigonometric_Equations.pdf"),
        "out": ROOT / "2024-apr",
    },
    {
        "id": "2025-jan",
        "kind": "chapterwise",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "out": ROOT / "2025-jan",
    },
    {
        "id": "2025-apr",
        "kind": "chapterwise",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "out": ROOT / "2025-apr",
    },
    {
        "id": "2026",
        "kind": "answers",
        "pdf": Path(r"C:\Users\tempo\Downloads\Maths\Trigonometric Equations\2026_Trigonometric_Equations.pdf"),
        "out": ROOT / "2026",
    },
]


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def fig_key(booklet: str, pdf_q: int) -> str:
    slug = booklet.replace("-", "")
    return f"s{slug}_te_q{pdf_q:02d}_1"


def inventory_keypage_solutions(pdf: Path) -> dict:
    """Answer Keys page that continues into `1. (key)` write-ups (2023 April)."""
    doc = pymupdf.open(pdf)
    answers_page = find_session_key_page(doc) or find_answers_solutions_page(doc)
    if not answers_page:
        doc.close()
        return inventory_session_solutions_pdf(pdf)
    keys, compact_bottom = parse_compact_answer_keys(doc[answers_page - 1])
    printed_qs = question_heading_anchors(doc, answers_page)
    printed_nos = sorted({q["q_no"] for q in printed_qs})
    sol_pages = list(range(answers_page, doc.page_count + 1))
    sol_anchors = solution_anchors(doc, answers_page, compact_bottom)
    plan_override = None
    if not sol_anchors and sorted(keys) == printed_nos == [1]:
        page = doc[answers_page - 1]
        sol_anchors = [{
            "page": answers_page,
            "q_no": 1,
            "y0": compact_bottom + 8,
            "y1": compact_bottom + 24,
            "heading": "1.",
            "printed_key": str(keys[1]),
        }]
        rec = {"title": TITLE, "pages": sol_pages, "questions": sol_anchors, "keys": keys}
        plan_override = crop_plan(rec)
        if plan_override:
            plan_override[0]["clip_y1"] = min(page.rect.y1 - 80, compact_bottom + 280)
            plan_override[0]["continues"] = False
            plan_override[0]["continuation"] = None
    rec = {"title": TITLE, "pages": sol_pages, "questions": sol_anchors, "keys": keys}
    plan = plan_override if plan_override is not None else crop_plan(rec)
    key_nos = sorted(keys)
    sol_nos = sorted({a["q_no"] for a in sol_anchors})
    crop_nos = sorted({s["q_no"] for s in plan})
    gate_ok = (
        printed_nos == key_nos == sol_nos == crop_nos
        and len(printed_nos) > 0
        and len(plan) == len(printed_nos)
    )
    chapter = {
        "title": TITLE,
        "pages": sol_pages,
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
        "style": "keypage-solutions",
        "key_page": answers_page,
        "key_pages": [answers_page],
        "chapters": [chapter],
        "printed_total": chapter["printed_count"],
        "key_total": chapter["key_count"],
        "crop_total": chapter["crop_count"],
        "gate_ok": gate_ok,
    }


def inventory_book(book: dict) -> dict:
    kind = book["kind"]
    if kind == "chapterwise":
        inv = inventory_chapterwise_solutions(book["pdf"], [TITLE])
    elif kind == "questionbank":
        inv = inventory_session_questionbank_solutions(book["pdf"])
    elif kind == "answers":
        inv = inventory_session_solutions_pdf(book["pdf"])
    else:
        inv = inventory_keypage_solutions(book["pdf"])
    ch = inv["chapters"][0]
    ch["title"] = TITLE
    dump(book["out"] / "inventory.json", paper.slim_report(inv))
    return inv


def render_book(book: dict, report: dict) -> None:
    dest = book["out"] / "crops"
    dest.mkdir(parents=True, exist_ok=True)
    figs = book["out"] / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    ch = report["chapters"][0]
    for spec in ch["crop_plan"]:
        pdf_q = int(spec["q_no"])
        render_crop(doc, spec, dest / f"te_q{pdf_q:02d}.png")
        paper.render_key_chip(doc, spec, dest / f"te_q{pdf_q:02d}_key.png")
        paper.extract_figure(doc, spec, figs / f"{fig_key(book['id'], pdf_q)}.png")
        print(f"  crop {book['id']} Q{pdf_q:02d} continues={spec['continues']}", flush=True)
    doc.close()


def fetch_rows(sb) -> dict[tuple[str, int], dict]:
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,source_bbox,review_status,body,solution_md,"
            "format,correct_option,numerical_answer"
        )
        .eq("chapter_id", chapter_id)
        .in_("review_status", ["auto_ok", "human_ok"])
        .execute()
        .data
        or []
    )
    out: dict[tuple[str, int], dict] = {}
    for row in rows:
        bbox = row.get("source_bbox") or {}
        booklet = str(bbox.get("booklet") or "")
        pdf_q = bbox.get("pdf_q")
        if booklet and pdf_q is not None:
            out[(booklet, int(pdf_q))] = row
    return out


def build_jobs(book: dict, report: dict, db_rows: dict) -> list[dict]:
    (book["out"] / "ocr").mkdir(parents=True, exist_ok=True)
    ch = report["chapters"][0]
    keys = {int(k): str(v) for k, v in ch["keys"].items()}
    jobs = []
    for spec in ch["crop_plan"]:
        pdf_q = int(spec["q_no"])
        row = db_rows.get((book["id"], pdf_q))
        kind, key = paper.official_key(row) if row else (
            "mcq" if keys.get(pdf_q) in {"1", "2", "3", "4"} else "numerical",
            keys.get(pdf_q, ""),
        )
        jobs.append({
            "booklet": book["id"],
            "section": "te",
            "pdf_q": pdf_q,
            "fig_key": fig_key(book["id"], pdf_q),
            "crop": book["out"] / "crops" / f"te_q{pdf_q:02d}.png",
            "key_png": book["out"] / "crops" / f"te_q{pdf_q:02d}_key.png",
            "fig_png": book["out"] / "figures" / f"{fig_key(book['id'], pdf_q)}.png",
            "cache": book["out"] / "ocr" / f"te_q{pdf_q:02d}.json",
            "kind": kind,
            "pdf_key": key or keys.get(pdf_q, ""),
            "row_id": None if row is None else row["id"],
            "db_q": None if row is None else row["q_no"],
        })
    return jobs


def tidy_te(md: str) -> str:
    body = paper.tidy_paper(md)
    body = paper.RUN_TITLE.sub("", body)
    body = __import__("re").sub(
        r"Trigonometric Equations|Questions with Solutions|"
        r"JEE Main 20\d{2}.*Question Bank|MathonGo",
        "",
        body,
        flags=__import__("re").I,
    )
    return __import__("re").sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def packet_for(item: dict) -> dict:
    pkt = paper.packet_for(item)
    if pkt.get("solution_md"):
        pkt["solution_md"] = tidy_te(pkt["solution_md"])
    return pkt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT.mkdir(parents=True, exist_ok=True)

    reports = {}
    failed = False
    for book in BOOKS:
        book["out"].mkdir(parents=True, exist_ok=True)
        report = inventory_book(book)
        reports[book["id"]] = report
        ch = report["chapters"][0]
        print(
            f"  {book['id']}: printed={ch['printed_count']} keys={ch['key_count']} "
            f"crops={ch['crop_count']} gate_ok={report['gate_ok']}",
            flush=True,
        )
        if not report["gate_ok"]:
            failed = True
    if failed:
        print("STOP: solution inventory gate failed", flush=True)
        return 2
    if args.inventory_only:
        return 0

    env = p.load_env()
    sb = p.supabase_client()
    db_rows = fetch_rows(sb)
    print(f"db live TE rows matched {len(db_rows)}", flush=True)

    books = {b["id"]: b for b in BOOKS}
    all_jobs = []
    if not args.publish_only:
        for book in BOOKS:
            render_book(book, reports[book["id"]])
            all_jobs.extend(build_jobs(book, reports[book["id"]], db_rows))
        results = paper.run_ocr(all_jobs, env)
        packets = [packet_for(item) for item in results]
        for book in BOOKS:
            dump(
                book["out"] / "packets.json",
                [pkt for pkt in packets if pkt["booklet"] == book["id"]],
            )
    else:
        packets = []
        for book in BOOKS:
            path = book["out"] / "packets.json"
            if path.exists():
                packets.extend(json.loads(path.read_text(encoding="utf-8")))

    if args.ocr_only:
        ok = sum(1 for pkt in packets if not pkt.get("hold"))
        print(f"OCR packets {ok}/{len(packets)}", flush=True)
        return 0 if ok == len(packets) else 2

    paper.upload_figures(sb, packets, env, books)
    live = 0
    holds = []
    for pkt in sorted(packets, key=lambda x: (x["booklet"], x["pdf_q"])):
        if pkt["hold"] or not pkt.get("solution_md"):
            holds.append(pkt)
            print(f"  [hold] {pkt['booklet']} Q{pkt['pdf_q']} {pkt.get('hold')}", flush=True)
            continue
        sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq(
            "id", pkt["row_id"]
        ).execute()
        live += 1
        print(f"  [paper] {pkt['booklet']} Q{pkt['pdf_q']} db={pkt['db_q']}", flush=True)
    dump(ROOT / "publish.json", {"written": live, "holds": len(holds)})
    print(f"paper solutions written={live} holds={len(holds)}", flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    raise SystemExit(main())
