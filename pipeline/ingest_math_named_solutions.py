#!/usr/bin/env python3
"""Paper OCR for named Maths chapter write-ups. gemma4. Never glm.

Crops the ANSWERS AND SOLUTIONS / footer Solutions band only.

    python ingest_math_named_solutions.py --inventory-only
    python ingest_math_named_solutions.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf

import ingest_math_2025_paper_solutions as paper
import ingest_math_named_ocr as named
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

SUBJECT = "Mathematics"
FILES = Path(r"c:\Users\tempo\Downloads\files")


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def fig_key(booklet: str, short: str, pdf_q: int, n: int = 1) -> str:
    slug = booklet.replace("-", "")
    return f"s{slug}_{short}_q{pdf_q:02d}_{n}"


def classify_session(pdf: Path) -> str:
    doc = pymupdf.open(pdf)
    text0 = (doc[0].get_text("text") or "").lower() if doc.page_count else ""
    answers = find_answers_solutions_page(doc)
    key = find_session_key_page(doc)
    n = doc.page_count
    doc.close()
    if "questions with solutions" in text0:
        return "keypage"
    if answers:
        return "answers"
    if "questions with answer keys" in text0 or key:
        # 2024-style: questions, compact key, then Solutions footer
        if key and key < n:
            return "questionbank"
        return "keypage"
    return "keypage"


def inventory_keypage_solutions(pdf: Path, title: str) -> dict:
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
    rec = {"title": title, "pages": sol_pages, "questions": sol_anchors, "keys": keys}
    plan = crop_plan(rec)
    key_nos = sorted(keys)
    sol_nos = sorted({a["q_no"] for a in sol_anchors})
    crop_nos = sorted({s["q_no"] for s in plan})
    gate_ok = (
        printed_nos == key_nos == sol_nos == crop_nos
        and len(printed_nos) > 0
        and len(plan) == len(printed_nos)
    )
    chapter = {
        "title": title,
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
    title = book["title"]
    if kind == "chapterwise":
        inv = inventory_chapterwise_solutions(book["pdf"], [title])
    elif kind == "questionbank":
        inv = inventory_session_questionbank_solutions(book["pdf"])
    elif kind == "answers":
        inv = inventory_session_solutions_pdf(book["pdf"])
    else:
        inv = inventory_keypage_solutions(book["pdf"], title)
    ch = inv["chapters"][0]
    ch["title"] = title
    dump(book["out"] / "inventory.json", paper.slim_report(inv))
    return inv


def render_book(book: dict, report: dict) -> None:
    dest = book["out"] / "crops"
    dest.mkdir(parents=True, exist_ok=True)
    figs = book["out"] / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    short = book["short"]
    doc = pymupdf.open(book["pdf"])
    ch = report["chapters"][0]
    for spec in ch["crop_plan"]:
        pdf_q = int(spec["q_no"])
        render_crop(doc, spec, dest / f"{short}_q{pdf_q:02d}.png")
        paper.render_key_chip(doc, spec, dest / f"{short}_q{pdf_q:02d}_key.png")
        paper.extract_figure(doc, spec, figs / f"{fig_key(book['id'], short, pdf_q)}.png")
        print(f"  crop {book['short']} {book['id']} Q{pdf_q:02d} continues={spec['continues']}", flush=True)
    doc.close()


def fetch_rows(sb, chapter_no: int) -> dict[tuple[str, int], dict]:
    chapter_id = p.resolve_chapter_id(sb, chapter_no, SUBJECT)
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
    short = book["short"]
    jobs = []
    for spec in ch["crop_plan"]:
        pdf_q = int(spec["q_no"])
        row = db_rows.get((book["id"], pdf_q))
        if row and str(row.get("solution_md") or "").strip():
            continue
        kind, key = paper.official_key(row) if row else (
            "mcq" if keys.get(pdf_q) in {"1", "2", "3", "4"} else "numerical",
            keys.get(pdf_q, ""),
        )
        jobs.append({
            "booklet": book["id"],
            "section": short,
            "pdf_q": pdf_q,
            "fig_key": fig_key(book["id"], short, pdf_q),
            "crop": book["out"] / "crops" / f"{short}_q{pdf_q:02d}.png",
            "key_png": book["out"] / "crops" / f"{short}_q{pdf_q:02d}_key.png",
            "fig_png": book["out"] / "figures" / f"{fig_key(book['id'], short, pdf_q)}.png",
            "cache": book["out"] / "ocr" / f"{short}_q{pdf_q:02d}.json",
            "kind": kind,
            "pdf_key": key or keys.get(pdf_q, ""),
            "row_id": None if row is None else row["id"],
            "db_q": None if row is None else row["q_no"],
        })
    return jobs


TITLE_STRIP = re.compile(
    r"Questions with (?:Answer Keys|Solutions)|JEE Main 20\d{2}.*Question Bank|MathonGo|"
    r"#PaperPhodnaHai|#MathBoleTohMathonGo",
    re.I,
)


def tidy_named(md: str, title: str) -> str:
    body = paper.tidy_paper(md)
    body = paper.RUN_TITLE.sub("", body)
    body = TITLE_STRIP.sub("", body)
    body = re.sub(re.escape(title), "", body, flags=re.I)
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def packet_for(item: dict, title: str) -> dict:
    pkt = paper.packet_for(item)
    if pkt.get("solution_md"):
        pkt["solution_md"] = tidy_named(pkt["solution_md"], title)
    return pkt


def upload_figures(sb, packets: list[dict], env: dict, books: dict) -> None:
    """books keyed by '{short}:{booklet}' so 2026 Circle does not steal 2026 AUC."""
    jobs = [
        pkt for pkt in packets
        if not pkt["hold"] and paper.ANY_FIG.search(pkt.get("solution_md") or "")
    ]
    if not jobs:
        return

    def one(pkt: dict) -> None:
        key = f"{pkt.get('section')}:{pkt['booklet']}"
        book = books.get(key)
        if book is None:
            return
        paper.upload_one_figure(sb, pkt, env, {pkt["booklet"]: book})

    with ThreadPoolExecutor(max_workers=min(32, max(1, len(jobs)))) as pool:
        list(pool.map(one, jobs))


def session_books_for(ch: dict) -> list[dict]:
    root = FILES / f"out-math-{ch['short']}-solutions"
    books = []
    for src in named.books_for(ch):
        kind = src["kind"]
        if kind == "session":
            kind = classify_session(src["pdf"])
        books.append({
            **src,
            "kind": kind,
            "out": root / src["id"],
        })
    return books


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    ap.add_argument("--chapters", default="")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    want = named.CHAPTERS
    if args.chapters.strip():
        nos = {int(x) for x in args.chapters.split(",") if x.strip()}
        want = [c for c in named.CHAPTERS if c["no"] in nos]

    all_books = []
    for ch in want:
        all_books.extend(session_books_for(ch))

    print(f"solution inventory {len(all_books)} PDFs", flush=True)
    reports = {}
    failed = False
    skipped = []
    for book in all_books:
        book["out"].mkdir(parents=True, exist_ok=True)
        try:
            report = inventory_book(book)
        except Exception as exc:
            skipped.append((book, str(exc)))
            print(f"  [skip] {book['short']} {book['id']}: {exc}", flush=True)
            continue
        reports[(book["chapter_no"], book["id"])] = report
        ch = report["chapters"][0]
        empty = ch["printed_count"] == 0 and ch["key_count"] == 0
        print(
            f"  {book['short']} {book['id']} kind={book['kind']}: "
            f"printed={ch['printed_count']} keys={ch['key_count']} "
            f"crops={ch['crop_count']} gate_ok={report['gate_ok']}"
            + (" skip-empty" if empty else ""),
            flush=True,
        )
        if empty:
            reports.pop((book["chapter_no"], book["id"]), None)
            continue
        if not report["gate_ok"]:
            print(f"  [glm-later] {book['short']} {book['id']} paper gate failed", flush=True)
            reports.pop((book["chapter_no"], book["id"]), None)
            skipped.append((book, "gate"))
            continue
    if args.inventory_only:
        return 0

    env = p.load_env()
    sb = p.supabase_client()
    all_jobs = []
    packets = []
    if not args.publish_only:
        for book in all_books:
            key = (book["chapter_no"], book["id"])
            if key not in reports:
                continue
            render_book(book, reports[key])
            db_rows = fetch_rows(sb, book["chapter_no"])
            all_jobs.extend(build_jobs(book, reports[key], db_rows))
        results = paper.run_ocr(all_jobs, env)
        title_by_short = {c["short"]: c["title"] for c in want}
        packets = [packet_for(item, title_by_short[item["job"]["section"]]) for item in results]
        by_book: dict[tuple[int, str], list] = {}
        for pkt in packets:
            job = next(j for j in all_jobs if j["booklet"] == pkt["booklet"] and j["pdf_q"] == pkt["pdf_q"] and j["section"] == pkt.get("section", j["section"]))
            by_book.setdefault((job["section"], pkt["booklet"]), []).append(pkt)
        for book in all_books:
            dump(book["out"] / "packets.json", [
                pkt for pkt in packets
                if pkt["booklet"] == book["id"] and pkt.get("section") == book["short"]
            ])
    else:
        for book in all_books:
            path = book["out"] / "packets.json"
            if path.exists():
                packets.extend(json.loads(path.read_text(encoding="utf-8")))

    if args.ocr_only:
        ok = sum(1 for pkt in packets if not pkt.get("hold"))
        print(f"OCR packets {ok}/{len(packets)}", flush=True)
        return 0 if ok == len(packets) else 2

    books = {f"{b['short']}:{b['id']}": b for b in all_books}
    upload_figures(sb, packets, env, books)
    live = 0
    holds = []
    for pkt in sorted(packets, key=lambda x: (x.get("section", ""), x["booklet"], x["pdf_q"])):
        if pkt["hold"] or not pkt.get("solution_md") or not pkt.get("row_id"):
            holds.append(pkt)
            print(f"  [hold] {pkt.get('section')} {pkt['booklet']} Q{pkt['pdf_q']} {pkt.get('hold')}", flush=True)
            continue
        sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq(
            "id", pkt["row_id"]
        ).execute()
        live += 1
        print(f"  [paper] {pkt.get('section')} {pkt['booklet']} Q{pkt['pdf_q']} db={pkt['db_q']}", flush=True)
    dump(FILES / "out-math-named-solutions" / "publish.json", {"written": live, "holds": len(holds)})
    print(f"paper solutions written={live} holds={len(holds)}", flush=True)
    return 0 if not holds else 2


if __name__ == "__main__":
    raise SystemExit(main())
