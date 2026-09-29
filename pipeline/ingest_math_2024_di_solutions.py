#!/usr/bin/env python3
"""Paper OCR for 2024 January / April Definite Integration question-bank write-ups.

Printed solutions sit after the Answer Key as Q1 / Q2 (not 1. (key)).
gemma4 only. Never glm. Never rewrites stems. PDF image xref figures.

    python ingest_math_2024_di_solutions.py
    python ingest_math_2024_di_solutions.py --inventory-only
    python ingest_math_2024_di_solutions.py --ocr-only
    python ingest_math_2024_di_solutions.py --publish-only
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
import pymupdf

import pyq_common as p
from agents.katex_check import katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from ingest_math_2025_paper_solutions import extract_figure, ocr_json
from ingest_math_2026_jan_di_solutions import (
    ANY_FIG,
    OCR_SYSTEM,
    PAPER_MARKER,
    assemble_solution_md,
    dump,
    ocr_matches_key,
    two_image_message,
)
from pyq_ocr_inventory import (
    DPI,
    inventory_session_questionbank_solutions,
    render_crop,
)

CHAPTER_NO = 17
SUBJECT = "Mathematics"
FIGURE_PREFIX = "math/figures"
ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2024-di-solutions")
EXPECT = {"2024-jan": 20, "2024-apr": 14}
BOOKS = [
    {
        "id": "2024-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-jan-di-solutions"),
    },
    {
        "id": "2024-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-apr-di-solutions"),
    },
]
BARE_Q = re.compile(r"^Q\s*\d{1,2}$", re.I)
RUN_JUNK = re.compile(
    r"^(?:Definite Integration|Solutions|Questions(?: with Answer Keys)?|"
    r"JEE Main 2024 (?:January|April) Question Bank|MathonGo|"
    r"#?MathBoleTohMathonGo|www\.mathongo\.com|"
    r"Do you want to practice.*|Click here to download MARKS App)\s*$",
    re.I,
)


def fig_stem(booklet: str, pdf_q: int) -> str:
    tag = "j" if booklet.endswith("jan") else "a"
    return f"s2024{tag}_q{pdf_q:02d}"


def fig_key(booklet: str, pdf_q: int) -> str:
    return f"{fig_stem(booklet, pdf_q)}_1"


def slim_report(report: dict) -> dict:
    ch = report["chapters"][0]
    return {k: v for k, v in report.items() if k != "chapters"} | {
        "chapters": [{kk: vv for kk, vv in ch.items() if kk != "questions"}]
    }


def kind_of(raw: str) -> tuple[str, str]:
    key = re.sub(r"[()]", "", str(raw or "")).strip()
    if key in {"1", "2", "3", "4"}:
        return "mcq", key
    return "numerical", key


def crop_key_strip(doc, key_page: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    page = doc[key_page - 1]
    scale = pymupdf.Matrix(DPI / 72, DPI / 72)
    page.get_pixmap(matrix=scale, alpha=False).save(str(dest))
    return dest


def render_book(book: dict, report: dict) -> None:
    dest = book["out"] / "crops"
    figs = book["out"] / "figures"
    dest.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    crop_key_strip(doc, int(report["key_page"]), dest / "answer_key.png")
    specs = []
    for spec in report["chapters"][0]["crop_plan"]:
        pdf_q = int(spec["q_no"])
        render_crop(doc, spec, dest / f"sol_q{pdf_q:02d}.png")
        specs.append(spec)
        print(f"  crop {book['id']} Q{pdf_q:02d} continues={spec['continues']}", flush=True)
    doc.close()

    def one(spec: dict) -> None:
        pdf_q = int(spec["q_no"])
        local = figs / f"{fig_key(book['id'], pdf_q)}.png"
        d = pymupdf.open(book["pdf"])
        try:
            ok = extract_figure(d, spec, local)
        finally:
            d.close()
        if not ok and local.exists():
            local.unlink()
        print(f"  xref {book['id']} Q{pdf_q:02d} {ok}", flush=True)

    with ThreadPoolExecutor(max_workers=len(specs)) as pool:
        list(pool.map(one, specs))


def fetch_rows(sb, chapter_id: int) -> dict[tuple[str, int], dict]:
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,exam_shift,source_bbox,review_status,"
            "body,solution_md,format,correct_option,numerical_answer"
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
        if booklet not in EXPECT or pdf_q is None:
            continue
        out[(booklet, int(pdf_q))] = row
    return out


def official_key(row: dict, fallback: str) -> tuple[str, str]:
    if str(row.get("format") or "") == "numerical":
        return "numerical", str(row.get("numerical_answer") or fallback).strip()
    choice = str(row.get("correct_option") or "").strip()
    if choice:
        return "mcq", choice
    return kind_of(fallback)


def tidy(md: str) -> str:
    body = re.sub(r"<!--\s*paper-ocr\s*-->", "", md or "")
    keep = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or RUN_JUNK.match(line) or BARE_Q.fullmatch(line):
            continue
        keep.append(line)
    return "\n".join(keep)


def build_jobs(book: dict, report: dict, db_rows: dict) -> list[dict]:
    (book["out"] / "ocr").mkdir(parents=True, exist_ok=True)
    keys = {int(k): str(v) for k, v in report["chapters"][0]["keys"].items()}
    jobs = []
    for spec in report["chapters"][0]["crop_plan"]:
        pdf_q = int(spec["q_no"])
        row = db_rows.get((book["id"], pdf_q))
        kind, key = official_key(row, keys.get(pdf_q, "")) if row else kind_of(keys.get(pdf_q, ""))
        jobs.append({
            "booklet": book["id"],
            "pdf_q": pdf_q,
            "fig_key": fig_key(book["id"], pdf_q),
            "crop": book["out"] / "crops" / f"sol_q{pdf_q:02d}.png",
            "key_png": book["out"] / "crops" / "answer_key.png",
            "fig_png": book["out"] / "figures" / f"{fig_key(book['id'], pdf_q)}.png",
            "cache": book["out"] / "ocr" / f"q_{pdf_q:02d}.json",
            "kind": kind,
            "pdf_key": key or keys.get(pdf_q, ""),
            "row_id": None if row is None else row["id"],
            "db_q": None if row is None else row["q_no"],
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
        f"Transcribe ONLY the printed solution for {job['booklet']} Q{job['pdf_q']} from image 1. "
        f"Official key is ({job['pdf_key']}), type {job['kind']}. "
        "Do not copy the listing header Qn. Text first: every printed label and formula. "
        "Never skip a continued-equals line under the first formula. "
        f"If and only if there are graphs/sketches, insert one [[fig:{fig_stem(job['booklet'], job['pdf_q'])}_N]] "
        "token per printed sketch, top-to-bottom then left-to-right, on its own line. "
        "Never keep only the largest diagram. Never attach the whole page as a figure. "
        "Never copy watermarks or page titles. Never rewrite a printed piecewise to a simplified line."
    )
    messages = [{"role": "system", "content": OCR_SYSTEM}]
    messages.extend(two_image_message(job["crop"], job["key_png"], prompt))
    last_err = None
    for _ in range(3):
        try:
            data = ocr_json(messages, env, limiter)
            data["_model"] = VISION_MODEL
            dump(cache, data)
            return data
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"{job['booklet']} Q{job['pdf_q']}: {last_err}")


def run_ocr(jobs: list[dict], env: dict) -> list[dict]:
    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} OCR jobs in parallel | model={VISION_MODEL}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(ocr_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            label = f"{job['booklet']} Q{job['pdf_q']}"
            try:
                data = fut.result()
                results.append({"ok": True, "job": job, "data": data})
                print(f"  [{'cached' if data.get('_cached') else 'ok'}] {label}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "job": job, "error": str(exc)})
                print(f"  [fail] {label} {exc}", flush=True)
    fails = [r for r in results if not r["ok"]]
    if fails:
        print(f"retry wave {len(fails)}", flush=True)
        with ThreadPoolExecutor(max_workers=max(1, len(fails))) as pool:
            futs = {pool.submit(ocr_one, r["job"], env, limiter): r for r in fails}
            for fut in as_completed(futs):
                prev = futs[fut]
                job = prev["job"]
                try:
                    data = fut.result()
                    prev["ok"] = True
                    prev["data"] = data
                    prev.pop("error", None)
                    print(f"  [retry-ok] {job['booklet']} Q{job['pdf_q']}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] {job['booklet']} Q{job['pdf_q']} {exc}", flush=True)
    return results


def packet_for(item: dict) -> dict:
    job = item["job"]
    hold = None
    md = ""
    answer = ""
    has_fig = job["fig_png"].exists()
    if not item.get("ok"):
        hold = item.get("error") or "ocr_fail"
    elif job["row_id"] is None:
        hold = "missing_row"
    else:
        data = item.get("data") or {}
        answer = str(data.get("answer") or "").strip()
        raw_md = tidy(str(data.get("markdown") or data.get("text") or ""))
        if not raw_md:
            hold = "empty_markdown"
        else:
            fig_files = sorted(
                (job["fig_png"].parent).glob(f"{fig_stem(job['booklet'], job['pdf_q'])}_*.png"),
                key=lambda path: int(path.stem.rsplit("_", 1)[-1]),
            )
            has_fig = bool(fig_files)
            has_diagram = bool(data.get("has_diagram")) or has_fig
            if fig_files and not ANY_FIG.search(raw_md):
                raw_md = "\n".join(f"[[fig:{path.stem}]]" for path in fig_files) + "\n" + raw_md
            if not has_fig:
                has_diagram = False
            md = assemble_solution_md(job["pdf_q"], raw_md, has_diagram=has_diagram)
            md = f"{PAPER_MARKER}\n\n{tidy(md)}\n"
            if not ocr_matches_key(answer, md, job["kind"], job["pdf_key"]):
                hold = f"key_mismatch ocr={answer!r} pdf={job['pdf_key']}"
            elif not katex_render_ok(md):
                hold = "katex_render"
    return {
        "booklet": job["booklet"],
        "pdf_q": job["pdf_q"],
        "fig_key": job["fig_key"],
        "kind": job["kind"],
        "pdf_key": job["pdf_key"],
        "ocr_answer": answer,
        "row_id": job["row_id"],
        "db_q": job["db_q"],
        "has_figure": has_fig,
        "solution_md": None if hold else md,
        "hold": hold,
    }


def upload_one(sb, pkt: dict, env: dict, books: dict) -> list[dict]:
    if pkt["hold"] or not ANY_FIG.search(pkt.get("solution_md") or ""):
        return []
    book = books[pkt["booklet"]]
    stem = fig_stem(pkt["booklet"], int(pkt["pdf_q"]))
    locals_ = sorted(
        (book["out"] / "figures").glob(f"{stem}_*.png"),
        key=lambda path: int(path.stem.rsplit("_", 1)[-1]),
    )
    if not locals_:
        pkt["solution_md"] = ANY_FIG.sub("", pkt["solution_md"] or "")
        return []
    uploaded: list[dict] = []
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    for local in locals_:
        object_name = f"{FIGURE_PREFIX}/{local.stem}.png"
        last_err = None
        for attempt in range(3):
            try:
                sb.storage.from_(p.BUCKET).upload(
                    object_name,
                    local.read_bytes(),
                    {
                        "content-type": mimetypes.guess_type(local.name)[0] or "image/png",
                        "upsert": "true",
                    },
                )
                last_err = None
                break
            except Exception as exc:
                last_err = exc
                time.sleep(1.5 * (attempt + 1))
        if last_err is not None:
            print(f"  skip figure {local.stem} {last_err}", flush=True)
            continue
        url = f"{base}/storage/v1/object/public/{p.BUCKET}/{object_name}"
        r = httpx.get(url, timeout=30.0)
        if r.status_code != 200 or r.content != local.read_bytes():
            print(f"  skip figure {local.stem} GET {r.status_code}", flush=True)
            continue
        print(f"  storage {local.stem} GET {r.status_code} {len(r.content)}B", flush=True)
        uploaded.append({"figure_key": local.stem, "url": url, "bytes": local.stat().st_size})
    if not uploaded:
        pkt["solution_md"] = ANY_FIG.sub("", pkt.get("solution_md") or "")
    return uploaded


def upload_figures(sb, packets: list[dict], env: dict, books: dict) -> None:
    jobs = [pkt for pkt in packets if not pkt["hold"] and ANY_FIG.search(pkt.get("solution_md") or "")]
    uploaded: list[dict] = []
    if jobs:
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            futs = [pool.submit(upload_one, sb, pkt, env, books) for pkt in jobs]
            for fut in as_completed(futs):
                uploaded.extend(fut.result() or [])
    dump(ROOT / "figure_uploads.json", uploaded)


def publish_packets(sb, packets: list[dict]) -> dict:
    for pkt in packets:
        if pkt.get("row_id"):
            sb.table("pyq_questions").update({"solution_md": None}).eq("id", pkt["row_id"]).execute()
            print(f"  cleared {pkt['booklet']} Q{pkt['pdf_q']}", flush=True)
    live = 0
    holds = []
    written = []
    for pkt in sorted(packets, key=lambda x: (x["booklet"], x["pdf_q"])):
        if pkt["hold"] or not pkt.get("solution_md") or not pkt.get("row_id"):
            holds.append({
                "booklet": pkt["booklet"],
                "pdf_q": pkt["pdf_q"],
                "reason": pkt["hold"] or "empty",
            })
            print(f"  [hold] {pkt['booklet']} Q{pkt['pdf_q']} {pkt['hold']}", flush=True)
            continue
        sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq(
            "id", pkt["row_id"]
        ).execute()
        live += 1
        written.append({
            "booklet": pkt["booklet"],
            "pdf_q": pkt["pdf_q"],
            "db_q": pkt["db_q"],
            "id": pkt["row_id"],
        })
        print(f"  [paper] {pkt['booklet']} Q{pkt['pdf_q']} db={pkt['db_q']}", flush=True)
    summary = {"written": live, "holds": holds, "rows": written, "total": len(packets)}
    dump(ROOT / "publish.json", summary)
    return summary


def load_packets() -> list[dict]:
    packets = []
    for book in BOOKS:
        path = book["out"] / "packets.json"
        if path.exists():
            packets.extend(json.loads(path.read_text(encoding="utf-8")))
    return packets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ROOT.mkdir(parents=True, exist_ok=True)
    reports = {}
    all_jobs = []
    for book in BOOKS:
        book["out"].mkdir(parents=True, exist_ok=True)
        report = inventory_session_questionbank_solutions(book["pdf"])
        dump(book["out"] / "inventory.json", slim_report(report))
        ch = report["chapters"][0]
        print(
            f"{book['id']} printed={report['printed_total']} keys={report['key_total']} "
            f"sols={report['solution_total']} crops={report['crop_total']} gate={report['gate_ok']}",
            flush=True,
        )
        if not report["gate_ok"] or report["printed_total"] != EXPECT[book["id"]]:
            print(f"  printed={ch['printed']} keys={sorted(ch['keys'])} sols={ch.get('solutions')}", flush=True)
            raise SystemExit(f"{book['id']} inventory gate failed")
        reports[book["id"]] = report
    if args.inventory_only:
        return 0

    env = p.load_env()
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db_rows = fetch_rows(sb, chapter_id)
    print(f"db live 2024 DI rows matched {len(db_rows)}", flush=True)
    need = sum(EXPECT.values())
    if len(db_rows) != need:
        raise SystemExit(f"expected {need} live 2024-jan/apr DI rows, got {len(db_rows)}")

    if not args.publish_only:
        for book in BOOKS:
            render_book(book, reports[book["id"]])
            jobs = build_jobs(book, reports[book["id"]], db_rows)
            missing = [j for j in jobs if not j["crop"].exists() or not j["key_png"].exists()]
            if missing:
                raise SystemExit(f"missing crops {[ (j['booklet'], j['pdf_q']) for j in missing ]}")
            all_jobs.extend(jobs)
        results = run_ocr(all_jobs, env)
        packets = [packet_for(r) for r in results]
        for book in BOOKS:
            dump(book["out"] / "packets.json", [p_ for p_ in packets if p_["booklet"] == book["id"]])
        dump(ROOT / "packets.json", packets)
        if args.ocr_only:
            holds = [p_ for p_ in packets if p_["hold"]]
            print(f"ocr packets {len(packets) - len(holds)}/{len(packets)} holds {len(holds)}", flush=True)
            return 0 if not holds else 2
    else:
        packets = load_packets()
        if not packets:
            raise SystemExit("no packets.json — run OCR first")

    books = {b["id"]: b for b in BOOKS}
    upload_figures(sb, packets, env, books)
    summary = publish_packets(sb, packets)
    print(
        f"written {summary['written']}/{summary['total']} holds {len(summary['holds'])}",
        flush=True,
    )
    return 0 if summary["written"] == summary["total"] and not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
