#!/usr/bin/env python3
"""OCR-first rebuild of 2025 Definite Integration from the Jan / April chapter-wise PDFs.

gemma4 reads one question crop + that Q's official key strip. Document AI is not first.
Parallel: one worker per question. Isolated caches under out-math-2025-*-di/.

    python ingest_math_2025_di_ocr.py
    python ingest_math_2025_di_ocr.py --inventory-only
    python ingest_math_2025_di_ocr.py --ocr-only
    python ingest_math_2025_di_ocr.py --publish-only
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from agents.publish import shape_ok_for, upsert_question
from audit_paper_text import flags_for
from format_ocr_math import format_ocr_math
from pyq_ocr_inventory import inventory_pdf
from run_chapter_agents import v2_json

DPI = 200
CHAPTER_NO = 17
SUBJECT = "Mathematics"
NAMED_COUNTS = {"2025-jan": 37, "2025-apr": 28}

BOOKS = [
    {
        "id": "2025-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di"),
        "month_date": "2025-01-01",
        "key_hint": 67,
    },
    {
        "id": "2025-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-apr-di"),
        "month_date": "2025-04-01",
        "key_hint": 64,
    },
]

Q_LINE = re.compile(r"^Q\s*(\d+)\s*\.\s*")
KEY_ITEM = re.compile(r"(\d{1,2})\s*\.\s*\(([^)]+)\)")
DI_HDR = re.compile(r"definite\s+integration", re.I)
INDEF_HDR = re.compile(r"indefinite\s+integration", re.I)
AUC_HDR = re.compile(r"area\s+under\s+curves?", re.I)
NEXT_CHAP = re.compile(
    r"area\s+under\s+curves?|differential\s+equations|straight\s+lines",
    re.I,
)

OCR_SYSTEM = """You look at one printed JEE Main PYQ packet: image 1 is the question crop (full width, both columns), image 2 is that question's official answer-key strip.
Return JSON only:
{"pdf_q_no":int,"exam_date":"YYYY-MM-DD"|null,"exam_shift":"morning"|"evening"|null,"format":"mcq"|"numerical","body":str,"options":[str,str,str,str]|[],"correct_option":"1"|"2"|"3"|"4"|null,"numerical_answer":str|null}
Transcribe the printed stem and options exactly. Keep every bound, modulus, GIF [x], remainder, and formula. Use $...$ KaTeX for math.
JSON strings must double every TeX backslash: \\int \\frac \\sqrt \\text \\to \\infty. Never write int_ or \\\\int.
Two radicals with + between them are $\\sqrt{A}+\\sqrt{B}$, never nested unless one printed bar covers both. Superscripts are ^{n}, never \\cdot n.
Paper-only: no solver talk, no book title, no MathonGo, no page numbers.
If the crop only says January 2025 or April 2025 with no day or shift, set exam_date and exam_shift to null.
Copy the official key from image 2 (and the prompt). Do not solve. Do not invent a question."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def page_text(page) -> str:
    return page.get_text("text") or ""


def has_title_line(text: str, title: re.Pattern) -> bool:
    for line in text.splitlines():
        if title.fullmatch(line.strip()):
            return True
    return False


def is_di_page(page) -> bool:
    text = page_text(page)
    return has_title_line(text, re.compile(r"definite\s+integration", re.I)) and not has_title_line(
        text, re.compile(r"indefinite\s+integration", re.I)
    )


def is_auc_page(page) -> bool:
    return has_title_line(page_text(page), re.compile(r"area\s+under\s+curves?", re.I))


def is_questions_half(page_no: int, key_page: int) -> bool:
    return page_no < key_page


def find_key_page(doc, hint: int) -> int:
    start = max(1, hint - 2)
    end = min(doc.page_count, hint + 4)
    for i in range(start, end + 1):
        text = doc[i - 1].get_text("text") or ""
        if DI_HDR.search(text) and KEY_ITEM.search(text):
            return i
    for i in range(1, doc.page_count + 1):
        text = doc[i - 1].get_text("text") or ""
        if "Answer Keys" in text[:80]:
            continue
        if DI_HDR.search(text) and KEY_ITEM.search(text) and i > 50:
            return i
    return hint


def parse_di_keys(text: str) -> dict[int, str]:
    low = text.lower()
    start = low.find("definite integration")
    if start < 0:
        return {}
    chunk = text[start:]
    stop = NEXT_CHAP.search(chunk[20:])
    if stop:
        chunk = chunk[: 20 + stop.start()]
    keys = {}
    for m in KEY_ITEM.finditer(chunk):
        keys[int(m.group(1))] = m.group(2).strip()
    return keys


def q_anchors(page) -> list[dict]:
    anchors = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines") or []:
            txt = "".join(s.get("text") or "" for s in line.get("spans") or []).strip()
            m = Q_LINE.match(txt)
            if not m:
                continue
            x0, y0, x1, y1 = line["bbox"]
            if x0 > page.rect.width * 0.55:
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


def inventory_book(book: dict, titles: list[str] | None = None) -> dict:
    want = titles or ["Definite Integration"]
    inv = inventory_pdf(Path(book["pdf"]), want)
    by_title = {c["title"]: c for c in inv["chapters"]}
    di = by_title.get("Definite Integration") or {
        "pages": [], "questions": [], "printed": [], "keys": {},
        "printed_count": 0, "key_count": 0, "gate_ok": False, "crop_count": 0,
    }
    named = NAMED_COUNTS[book["id"]]
    report = {
        "id": book["id"],
        "pdf": str(book["pdf"]),
        "key_page": inv["key_page"],
        "key_pages": inv["key_pages"],
        "di_pages": di.get("pages") or [],
        "questions": di.get("questions") or [],
        "printed_q_nos": di.get("printed") or [],
        "printed_count": di.get("printed_count") or 0,
        "named_expect": named,
        "answer_keys": di.get("keys") or {},
        "key_count": di.get("key_count") or 0,
        "crop_count": di.get("crop_count") or 0,
        "inventory": inv,
        "gate_ok": bool(inv["gate_ok"] and di.get("gate_ok")),
        "named_mismatch": named != (inv["printed_total"] if len(want) > 1 else di.get("printed_count") or 0),
        "note": (
            f"Printed {', '.join(want)} is {inv['printed_total']} questions "
            f"(answer key {inv['key_total']}, crops {inv['crop_total']}). "
            f"Named {named} is the TOC/block total — inventory every title in scope."
        ),
    }
    out = book["out"]
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "inventory.json", {
        k: v for k, v in report.items()
        if k != "inventory"
    } | {
        "chapters": [
            {kk: vv for kk, vv in c.items() if kk not in ("questions", "crop_plan")}
            for c in inv["chapters"]
        ]
    })
    dump(out / "answer_key.json", di.get("keys") or {})
    return report


def crop_key_strip(book: dict, keys: dict[int, str], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[find_key_page(doc, book["key_hint"]) - 1]
    hits = page.search_for("Definite Integration")
    if not hits:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), alpha=False)
        pix.save(str(dest))
        doc.close()
        return dest
    start = min(hits, key=lambda r: r.y0)
    nxt = page.search_for("Area Under")
    y1 = min(h.y0 for h in nxt) if nxt else min(page.rect.y1, start.y0 + 80)
    clip = pymupdf.Rect(page.rect.x0, max(page.rect.y0, start.y0 - 4), page.rect.x1, y1)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip, alpha=False)
    pix.save(str(dest))
    doc.close()
    return dest


def stitch(pixes: list[pymupdf.Pixmap], dest: Path) -> Path:
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


def crop_question(book: dict, rec: dict, by_page: dict[int, list[dict]], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    page = doc[rec["page"] - 1]
    y0 = max(page.rect.y0 + 40, rec["y0"] - 6)
    later = [a for a in by_page.get(rec["page"], []) if a["q_no"] > rec["q_no"] and a["y0"] > rec["y0"] + 4]
    if later:
        y1 = min(a["y0"] for a in later) - 4
        y1 = max(y1, y0 + 40)
        clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip, alpha=False)
        pix.save(str(dest))
        doc.close()
        return dest
    y1 = page.rect.y1 - 28
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
    pixes = [page.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=clip, alpha=False)]
    nxt_no = rec["page"] + 1
    if nxt_no <= doc.page_count and is_di_page(doc[nxt_no - 1]):
        nxt = doc[nxt_no - 1]
        nxt_anchors = q_anchors(nxt)
        cut = min((a["y0"] for a in nxt_anchors), default=nxt.rect.y0 + 220)
        cont = pymupdf.Rect(nxt.rect.x0, nxt.rect.y0 + 40, nxt.rect.x1, max(nxt.rect.y0 + 56, cut - 4))
        if cont.y1 - cont.y0 >= 16:
            pixes.append(nxt.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72), clip=cont, alpha=False))
            stitch(pixes, dest)
            doc.close()
            return dest
    pixes[0].save(str(dest))
    doc.close()
    return dest


def two_image_message(q_png: Path, key_png: Path, text: str) -> list:
    q_b64 = base64.b64encode(q_png.read_bytes()).decode("ascii")
    k_b64 = base64.b64encode(key_png.read_bytes()).decode("ascii")
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{q_b64}"}},
            {"type": "text", "text": "Official answer-key strip for this chapter (image 2):"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{k_b64}"}},
        ],
    }]


def refine_type(spec: dict, entry: dict) -> dict:
    raw = spec.get("raw_key")
    opts = entry.get("options")
    has_mcq = isinstance(opts, list) and len(opts) == 4 and all((o or "").strip() for o in opts)
    v = str(raw or "").strip().upper()
    if v in "ABCD":
        spec["answer_type"] = "mcq"
        spec["answer_value"] = str("ABCD".index(v) + 1)
        return spec
    if has_mcq and v.isdigit() and 1 <= int(v) <= 4:
        spec["answer_type"] = "mcq"
        spec["answer_value"] = v
        return spec
    spec["answer_type"] = "numerical"
    spec["answer_value"] = str(raw or "").strip()
    entry["options"] = []
    return spec


def clean_entry(raw: dict) -> dict:
    body = format_ocr_math(str(raw.get("body") or ""))
    opts = raw.get("options")
    if isinstance(opts, list) and len(opts) == 4:
        options = [format_ocr_math(str(o or "")) for o in opts]
    else:
        options = []
    return {"body": body, "options": options or None}


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
        "Keep every printed detail."
    )
    messages = [{"role": "system", "content": OCR_SYSTEM}]
    messages.extend(two_image_message(job["crop"], job["key_png"], prompt))
    last_err = None
    for _ in range(3):
        try:
            data = v2_json(VISION_MODEL, messages, env, limiter)
            data["_model"] = VISION_MODEL
            dump(cache, data)
            return data
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"{job['booklet']} Q{job['q_no']}: {last_err}")


def build_jobs(reports: list[dict]) -> list[dict]:
    jobs = []
    books = {b["id"]: b for b in BOOKS}
    for report in reports:
        book = books[report["id"]]
        out = book["out"]
        (out / "crops").mkdir(parents=True, exist_ok=True)
        (out / "ocr").mkdir(parents=True, exist_ok=True)
        key_png = crop_key_strip(book, report["answer_keys"], out / "crops" / "answer_key.png")
        by_page: dict[int, list[dict]] = {}
        for rec in report["questions"]:
            by_page.setdefault(rec["page"], []).append(rec)
        for rec in report["questions"]:
            q_no = rec["q_no"]
            crop = out / "crops" / f"q{q_no:02d}.png"
            crop_question(book, rec, by_page, crop)
            jobs.append({
                "booklet": book["id"],
                "q_no": q_no,
                "page": rec["page"],
                "crop": crop,
                "key_png": key_png,
                "raw_key": report["answer_keys"][q_no],
                "month_date": book["month_date"],
                "cache": out / "ocr" / f"q_{q_no:02d}.json",
                "out": out,
            })
    return jobs


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


def fetch_2025_rows(sb, chapter_id: int) -> dict[tuple[str, int], dict]:
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,exam_date,source_bbox,review_status,format")
        .eq("chapter_id", chapter_id)
        .gte("exam_date", "2025-01-01")
        .lt("exam_date", "2026-01-01")
        .execute()
        .data
        or []
    )
    out = {}
    for row in rows:
        bbox = row.get("source_bbox") or {}
        booklet = bbox.get("booklet")
        pdf_q = bbox.get("pdf_q")
        if booklet and pdf_q is not None:
            out[(booklet, int(pdf_q))] = row
    return out


def publish_results(sb, chapter_id: int, results: list[dict]) -> dict:
    db_rows = fetch_2025_rows(sb, chapter_id)
    live = 0
    holds = []
    for item in results:
        job = item["job"]
        key = (job["booklet"], job["q_no"])
        db = db_rows.get(key)
        if db is None:
            holds.append({**key, "reason": "no-db-row"})
            continue
        if not item.get("ok"):
            holds.append({**key, "reason": item.get("error")})
            continue
        raw = item["data"]
        entry = clean_entry(raw)
        spec = {
            "q_no": job["q_no"],
            "raw_key": job["raw_key"],
            "answer_type": "mcq",
            "answer_value": job["raw_key"],
        }
        spec = refine_type(spec, entry)
        if spec["answer_type"] == "numerical":
            entry["options"] = None
        date = raw.get("exam_date") if isinstance(raw.get("exam_date"), str) else None
        if not date or not re.match(r"2025-\d{2}-\d{2}$", date):
            date = job["month_date"]
        shift = raw.get("exam_shift")
        if shift not in ("morning", "evening"):
            shift = None
        dump(job["out"] / "parsed" / f"q_{job['q_no']:02d}.json", {
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
        print(f"  [{tag}] {job['booklet']} Q{job['q_no']} db={db['q_no']} {status}", flush=True)
        if status == "human_ok":
            live += 1
        else:
            holds.append({
                "booklet": job["booklet"], "pdf_q": job["q_no"], "db_q": db["q_no"],
                "shape_ok": shape_ok, "audit_ok": audit_ok, "katex_ok": katex_ok,
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

    print("inventory January + April in parallel", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(inventory_book, BOOKS))
    for r in reports:
        print(
            f"  {r['id']}: pages={r['di_pages']} printed={r['printed_count']} "
            f"keys={r['key_count']} named={r['named_expect']} gate_ok={r['gate_ok']}",
            flush=True,
        )
        print(f"    {r['note']}", flush=True)
        if not r["gate_ok"]:
            print("STOP: printed Q set does not match the chapter answer key.", flush=True)
            return 2
        if r["named_mismatch"]:
            print(
                f"    named {r['named_expect']} is the TOC/block total; "
                f"inventory every in-scope title (printed {r['printed_count']} in this run).",
                flush=True,
            )

    if args.inventory_only:
        return 0

    env = p.load_env()
    jobs = build_jobs(reports)
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di") / "jobs.json", [
        {k: (str(v) if isinstance(v, Path) else v) for k, v in j.items() if k != "data"}
        for j in jobs if j["booklet"] == "2025-jan"
    ])
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-apr-di") / "jobs.json", [
        {k: (str(v) if isinstance(v, Path) else v) for k, v in j.items() if k != "data"}
        for j in jobs if j["booklet"] == "2025-apr"
    ])
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
            dump(jobs[0]["out"].parent / "ocr_holds.json", [
                {"booklet": r["job"]["booklet"], "q": r["job"]["q_no"], "error": r.get("error")}
                for r in still
            ])
            print(f"OCR holds {len(still)} — not publishing those rows", flush=True)

    if args.ocr_only:
        ok = sum(1 for r in results if r.get("ok"))
        print(f"OCR done {ok}/{len(results)}", flush=True)
        return 0 if ok == len(results) else 2

    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    summary = publish_results(sb, chapter_id, results)
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di") / "publish.json", summary)
    print(f"published live={summary['live']} holds={len(summary['holds'])}", flush=True)
    return 0 if not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
