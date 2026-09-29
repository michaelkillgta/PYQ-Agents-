#!/usr/bin/env python3
"""OCR-first 2025 Area Under Curves + Differential Equations from the same Jan/April books.

Definite Integration (13+9) is already live. January's named 37 is DI+AUC+DE.
These extra rows land on area-under-curves (ch 18) and differential-equations (ch 19).
Never park them on Definite Integration. Never touch 2026 DI q_no 166-179.

    python ingest_math_2025_auc_de.py
    python ingest_math_2025_auc_de.py --inventory-only
    python ingest_math_2025_auc_de.py --ocr-only
    python ingest_math_2025_auc_de.py --publish-only
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
from pyq_ocr_inventory import inventory_pdf

CHAPTER_NO = 17
CHAPTER_NOS = {"auc": 18, "de": 19}
SUBJECT = "Mathematics"
Q_NO_START = 1
TAKE = (("auc", "Area Under Curves"), ("de", "Differential Equations"))
STOP_TITLE = re.compile(r"straight\s+lines", re.I)
TITLE_RES = {
    "indef": re.compile(r"indefinite\s+integration", re.I),
    "di": re.compile(r"definite\s+integration", re.I),
    "auc": re.compile(r"area\s+under\s+curves?", re.I),
    "de": re.compile(r"differential\s+equations?", re.I),
    "sl": STOP_TITLE,
}
KEY_TITLES = [
    ("indef", "Indefinite Integration"),
    ("di", "Definite Integration"),
    ("auc", "Area Under Curves"),
    ("de", "Differential Equations"),
    ("sl", "Straight Lines"),
]


def page_chapter(page) -> str | None:
    text = di.page_text(page)
    found: list[str] = []
    for cid, rx in TITLE_RES.items():
        for line in text.splitlines():
            t = line.strip()
            if not t:
                continue
            if rx.fullmatch(t):
                if cid == "di" and TITLE_RES["indef"].fullmatch(t):
                    continue
                found.append(cid)
                break
    for cid in ("auc", "de", "di", "indef", "sl"):
        if cid in found:
            return cid
    return None


def parse_section_keys(text: str, title: str, nxt: str) -> dict[int, str]:
    low = text.lower()
    start = low.find(title.lower())
    if start < 0:
        return {}
    chunk = text[start:]
    stop = chunk.lower().find(nxt.lower(), len(title))
    if stop > 0:
        chunk = chunk[:stop]
    keys = {}
    for m in di.KEY_ITEM.finditer(chunk):
        keys[int(m.group(1))] = m.group(2).strip()
    return keys


def inventory_book(book: dict) -> dict:
    titles = [title for _cid, title in TAKE]
    inv = inventory_pdf(Path(book["pdf"]), titles)
    by_title = {c["title"]: c for c in inv["chapters"]}
    sections = {}
    for cid, title in TAKE:
        rec = by_title.get(title) or {
            "pages": [], "questions": [], "printed": [], "keys": {}, "gate_ok": False,
        }
        questions = [
            {**q, "chapter": cid}
            for q in rec.get("questions") or []
        ]
        sections[cid] = {
            "title": title,
            "pages": rec.get("pages") or [],
            "questions": questions,
            "printed": rec.get("printed") or [],
            "keys": rec.get("keys") or {},
            "crop_count": rec.get("crop_count") or 0,
            "gate_ok": bool(rec.get("gate_ok")),
        }
    return {
        "id": book["id"],
        "key_page": inv["key_page"],
        "key_pages": inv["key_pages"],
        "sections": sections,
        "inventory": inv,
        "gate_ok": bool(inv["gate_ok"]),
        "count": inv["printed_total"],
    }


def crop_key_strip(book: dict, title: str, nxt: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[(68 if book["id"] == "2025-jan" else 65) - 1]
    hits = page.search_for(title)
    if not hits:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(di.DPI / 72, di.DPI / 72), alpha=False)
        pix.save(str(dest))
        doc.close()
        return dest
    start = min(hits, key=lambda r: r.y0)
    nxt_hits = page.search_for(nxt)
    y1 = min(h.y0 for h in nxt_hits) if nxt_hits else min(page.rect.y1, start.y0 + 120)
    clip = pymupdf.Rect(page.rect.x0, max(page.rect.y0, start.y0 - 4), page.rect.x1, y1)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(di.DPI / 72, di.DPI / 72), clip=clip, alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def crop_question(book: dict, rec: dict, by_page: dict, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[rec["page"] - 1]
    cid = rec["chapter"]
    y0 = max(page.rect.y0 + 40, rec["y0"] - 6)
    later = [
        a for a in by_page.get(rec["page"], [])
        if a["chapter"] == cid and a["q_no"] > rec["q_no"] and a["y0"] > rec["y0"] + 4
    ]
    if later:
        y1 = min(a["y0"] for a in later) - 4
        y1 = max(y1, y0 + 40)
        clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(di.DPI / 72, di.DPI / 72), clip=clip, alpha=False)
        pix.save(str(dest))
        doc.close()
        return dest
    y1 = page.rect.y1 - 28
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
    pixes = [page.get_pixmap(matrix=pymupdf.Matrix(di.DPI / 72, di.DPI / 72), clip=clip, alpha=False)]
    nxt_no = rec["page"] + 1
    if nxt_no <= doc.page_count and page_chapter(doc[nxt_no - 1]) == cid:
        nxt = doc[nxt_no - 1]
        nxt_anchors = [a for a in di.q_anchors(nxt)]
        cut = min((a["y0"] for a in nxt_anchors), default=nxt.rect.y0 + 220)
        cont = pymupdf.Rect(nxt.rect.x0, nxt.rect.y0 + 40, nxt.rect.x1, max(nxt.rect.y0 + 56, cut - 4))
        if cont.y1 - cont.y0 >= 16:
            pixes.append(nxt.get_pixmap(matrix=pymupdf.Matrix(di.DPI / 72, di.DPI / 72), clip=cont, alpha=False))
            di.stitch(pixes, dest)
            doc.close()
            return dest
    pixes[0].save(str(dest))
    doc.close()
    return dest


def build_jobs(reports: list[dict]) -> list[dict]:
    books = {b["id"]: b for b in di.BOOKS}
    jobs = []
    for report in reports:
        book = books[report["id"]]
        out = book["out"]
        (out / "crops").mkdir(parents=True, exist_ok=True)
        (out / "ocr").mkdir(parents=True, exist_ok=True)
        all_q = []
        for cid, title in TAKE:
            all_q.extend(report["sections"][cid]["questions"])
        by_page: dict[int, list[dict]] = {}
        for rec in all_q:
            by_page.setdefault(rec["page"], []).append(rec)
        for cid, title in TAKE:
            nxt = "Straight Lines" if cid == "de" else "Differential Equations"
            key_png = crop_key_strip(book, title, nxt, out / "crops" / f"key_{cid}.png")
            sec = report["sections"][cid]
            for rec in sec["questions"]:
                q_no = rec["q_no"]
                crop = out / "crops" / f"{cid}_q{q_no:02d}.png"
                crop_question(book, rec, by_page, crop)
                jobs.append({
                    "booklet": book["id"],
                    "chapter": cid,
                    "q_no": q_no,
                    "page": rec["page"],
                    "crop": crop,
                    "key_png": key_png,
                    "raw_key": sec["keys"][q_no],
                    "month_date": book["month_date"],
                    "cache": out / "ocr" / f"{cid}_q_{q_no:02d}.json",
                    "out": out,
                })
    return jobs


def run_ocr(jobs: list[dict], env: dict) -> list[dict]:
    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} OCR jobs in parallel | model={VISION_MODEL}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(di.ocr_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                data = fut.result()
                results.append({"ok": True, "job": job, "data": data})
                tag = "cached" if data.get("_cached") else "ok"
                print(f"  [{tag}] {job['booklet']} {job['chapter']} Q{job['q_no']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "job": job, "error": str(exc)})
                print(f"  [fail] {job['booklet']} {job['chapter']} Q{job['q_no']} {exc}", flush=True)
    fails = [r for r in results if not r["ok"]]
    if fails:
        print(f"retry wave {len(fails)}", flush=True)
        with ThreadPoolExecutor(max_workers=max(1, len(fails))) as pool:
            futs = {pool.submit(di.ocr_one, r["job"], env, limiter): r for r in fails}
            for fut in as_completed(futs):
                prev = futs[fut]
                try:
                    data = fut.result()
                    prev["ok"] = True
                    prev["data"] = data
                    prev.pop("error", None)
                    print(f"  [retry-ok] {prev['job']['booklet']} {prev['job']['chapter']} Q{prev['job']['q_no']}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] {prev['job']['booklet']} {prev['job']['chapter']} Q{prev['job']['q_no']} {exc}", flush=True)
    return results


def fetch_rows(sb, chapter_id: int) -> dict[tuple[str, str, int], dict]:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,source_bbox,review_status,format")
        .eq("chapter_id", chapter_id)
        .execute()
        .data
        or []
    )
    out = {}
    max_q = 0
    for row in rows:
        max_q = max(max_q, int(row["q_no"]))
        bbox = row.get("source_bbox") or {}
        booklet = bbox.get("booklet")
        chap = bbox.get("chapter")
        pdf_q = bbox.get("pdf_q")
        if booklet and chap and pdf_q is not None:
            out[(booklet, chap, int(pdf_q))] = row
    out["_max_q"] = max_q
    return out


def ensure_rows(sb, chapter_id: int, jobs: list[dict], db_rows: dict) -> dict:
    max_q = max(int(db_rows.get("_max_q") or 0), Q_NO_START - 1)
    seed = []
    for job in jobs:
        key = (job["booklet"], job["chapter"], job["q_no"])
        if key in db_rows:
            continue
        raw = job["raw_key"]
        kind = "mcq" if str(raw).strip() in {"1", "2", "3", "4"} else "numerical"
        max_q += 1
        seed.append({
            "chapter_id": chapter_id,
            "topic_id": None,
            "q_no": max_q,
            "tier": "must_do",
            "format": kind,
            "body": None,
            "correct_option": int(raw) if kind == "mcq" else None,
            "numerical_answer": None if kind == "mcq" else str(raw),
            "exam_date": job["month_date"],
            "exam_shift": None,
            "out_of_syllabus": False,
            "good_to_solve": False,
            "source_page": job["page"],
            "source_bbox": {
                "booklet": job["booklet"],
                "chapter": job["chapter"],
                "pdf_q": job["q_no"],
            },
            "review_status": "skeleton_only",
        })
        print(f"  insert {job['booklet']} {job['chapter']} Q{job['q_no']} as q_no {max_q}", flush=True)
    if seed:
        sb.table("pyq_questions").insert(seed).execute()
        return fetch_rows(sb, chapter_id)
    return db_rows


def publish_results(sb, chapter_id: int, results: list[dict]) -> dict:
    db_rows = fetch_rows(sb, chapter_id)
    jobs = [item["job"] for item in results]
    jobs.sort(key=lambda j: (j["booklet"], j["chapter"], j["q_no"]))
    db_rows = ensure_rows(sb, chapter_id, jobs, db_rows)
    live = 0
    holds = []
    for item in results:
        job = item["job"]
        key = (job["booklet"], job["chapter"], job["q_no"])
        db = db_rows.get(key)
        if db is None:
            holds.append({"key": key, "reason": "no-db-row"})
            continue
        if not item.get("ok"):
            holds.append({"key": key, "reason": item.get("error")})
            continue
        raw = item["data"]
        entry = di.clean_entry(raw)
        spec = {
            "q_no": job["q_no"],
            "raw_key": job["raw_key"],
            "answer_type": "mcq",
            "answer_value": job["raw_key"],
        }
        spec = di.refine_type(spec, entry)
        if spec["answer_type"] == "numerical":
            entry["options"] = None
        date = raw.get("exam_date") if isinstance(raw.get("exam_date"), str) else None
        if not date or not re.match(r"2025-\d{2}-\d{2}$", date):
            date = job["month_date"]
        shift = raw.get("exam_shift")
        if shift not in ("morning", "evening"):
            shift = None
        di.dump(job["out"] / "parsed" / f"{job['chapter']}_q_{job['q_no']:02d}.json", {
            "spec": spec, "entry": entry, "exam_date": date, "exam_shift": shift,
        })
        shape_ok = shape_ok_for(spec, entry)
        audit_ok = not flags_for(entry.get("body") or "", is_option=False)
        if entry.get("options"):
            audit_ok = audit_ok and all(not flags_for(o or "", is_option=True) for o in entry["options"])
        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        katex_ok = all(katex_render_ok(t) for t in fields)
        solver_dump = is_solver_dump(entry.get("body") or "")
        publishable = shape_ok and audit_ok and katex_ok and not solver_dump and spec.get("answer_value")
        status = "human_ok" if publishable else "unreviewed"
        fmt = spec["answer_type"]
        sb.table("pyq_questions").update({
            "format": fmt,
            "exam_date": date,
            "exam_shift": shift,
            "source_page": job["page"],
            "correct_option": int(spec["answer_value"]) if fmt == "mcq" and str(spec["answer_value"]).isdigit() else None,
            "numerical_answer": None if fmt == "mcq" else str(spec["answer_value"]),
        }).eq("id", db["id"]).execute()
        upsert_question(
            sb, db["id"], entry, status,
            1.0 if status == "human_ok" else 0.5,
            spec,
            answer=str(spec.get("answer_value") or ""),
        )
        if fmt == "numerical":
            sb.table("pyq_question_options").delete().eq("question_id", db["id"]).execute()
        tag = "LIVE" if status == "human_ok" else "HOLD"
        print(f"  [{tag}] {job['booklet']} {job['chapter']} Q{job['q_no']} db={db['q_no']} {status}", flush=True)
        if status == "human_ok":
            live += 1
        else:
            holds.append({
                "booklet": job["booklet"], "chapter": job["chapter"], "pdf_q": job["q_no"],
                "db_q": db["q_no"], "shape_ok": shape_ok, "audit_ok": audit_ok, "katex_ok": katex_ok,
                "preview": (entry.get("body") or "")[:160],
            })
    return {"live": live, "holds": holds}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    print("inventory AUC + DE January + April in parallel", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(inventory_book, di.BOOKS))
    for r in reports:
        bits = []
        for cid, _title in TAKE:
            s = r["sections"][cid]
            bits.append(f"{cid}={len(s['printed'])}/{len(s['keys'])} gate={s['gate_ok']}")
        print(f"  {r['id']}: {', '.join(bits)} total={r['count']} gate_ok={r['gate_ok']}", flush=True)
        if not r["gate_ok"]:
            print("STOP: printed Q set does not match the chapter answer key.", flush=True)
            di.dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di") / "auc_de_inventory.json", r)
            return 2

    di.dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di") / "auc_de_inventory.json", reports)
    if args.inventory_only:
        return 0

    env = p.load_env()
    jobs = build_jobs(reports)
    print(f"cropped {len(jobs)} questions", flush=True)

    if args.publish_only:
        results = []
        for job in jobs:
            cache = job["cache"]
            if not cache.exists():
                print(f"missing OCR cache {cache}", flush=True)
                return 2
            results.append({"ok": True, "job": job, "data": json.loads(cache.read_text(encoding="utf-8"))})
    else:
        results = run_ocr(jobs, env)
        still = [r for r in results if not r.get("ok")]
        if still:
            print(f"OCR holds {len(still)} — not publishing those rows", flush=True)

    if args.ocr_only:
        ok = sum(1 for r in results if r.get("ok"))
        print(f"OCR done {ok}/{len(results)}", flush=True)
        return 0 if ok == len(results) else 2

    sb = p.supabase_client()
    live = 0
    holds = []
    by_ch: dict[str, list] = {}
    for item in results:
        by_ch.setdefault(item["job"]["chapter"], []).append(item)
    for chap, items in by_ch.items():
        cid = p.resolve_chapter_id(sb, CHAPTER_NOS[chap], SUBJECT)
        part = publish_results(sb, cid, items)
        live += part["live"]
        holds.extend(part["holds"])
    summary = {"live": live, "holds": holds}
    di.dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di") / "auc_de_publish.json", summary)
    print(f"published live={summary['live']} holds={len(summary['holds'])}", flush=True)
    return 0 if not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
