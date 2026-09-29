#!/usr/bin/env python3
"""Paper OCR for 2025 January / April MathonGo chapter-wise write-ups.

DI + AUC + DE live rows only. gemma4. Never glm. Never rewrites stems.

    python ingest_math_2025_paper_solutions.py
    python ingest_math_2025_paper_solutions.py --inventory-only
    python ingest_math_2025_paper_solutions.py --ocr-only
    python ingest_math_2025_paper_solutions.py --publish-only
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
    inventory_chapterwise_solutions,
    normalize_printed_key,
    render_crop,
)
from run_chapter_agents import v2_json

CHAPTER_NO = 17
CHAPTER_NOS = {"di": 17, "auc": 18, "de": 19}
SUBJECT = "Mathematics"
FIGURE_PREFIX = "math/figures"
TITLES = [
    "Definite Integration",
    "Area Under Curves",
    "Differential Equations",
]
SECTION_SLUG = {
    "Definite Integration": "di",
    "Area Under Curves": "auc",
    "Differential Equations": "de",
}
EXPECT = {
    "2025-jan": {"di": 13, "auc": 12, "de": 12},
    "2025-apr": {"di": 9, "auc": 7, "de": 10},
}
BOOKS = [
    {
        "id": "2025-jan",
        "tag": "j",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-solutions"),
    },
    {
        "id": "2025-apr",
        "tag": "a",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-apr-solutions"),
    },
]
RUN_TITLE = re.compile(
    r"^(?:Definite Integration|Area Under Curves|Differential Equations|"
    r"Chapter-wise Question Bank|JEE Main 2025 (?:January|April)|MathonGo)\s*$",
    re.I | re.M,
)


def fig_key(booklet: str, section: str, pdf_q: int) -> str:
    tag = "j" if booklet.endswith("jan") else "a"
    return f"s2025{tag}_{section}_q{pdf_q:02d}_1"


def section_of(bbox: dict | None) -> str:
    raw = str((bbox or {}).get("chapter") or "").strip().lower()
    if raw in {"auc", "area under curves"}:
        return "auc"
    if raw in {"de", "differential equations"}:
        return "de"
    return "di"


def slim_report(report: dict) -> dict:
    chapters = []
    for ch in report["chapters"]:
        rec = {k: v for k, v in ch.items() if k != "questions"}
        chapters.append(rec)
    return {k: v for k, v in report.items() if k != "chapters"} | {"chapters": chapters}


def gate_book(book: dict, report: dict) -> None:
    want = EXPECT[book["id"]]
    print(
        f"{book['id']} printed={report['printed_total']} keys={report['key_total']} "
        f"crops={report['crop_total']} gate_ok={report['gate_ok']}",
        flush=True,
    )
    if not report["gate_ok"]:
        for ch in report["chapters"]:
            print(
                f"  {ch['title']} printed={ch['printed']} keys={sorted(ch['keys'])} "
                f"crops={ch['crop_count']} gate={ch['gate_ok']}",
                flush=True,
            )
        raise SystemExit(f"{book['id']} inventory gate failed")
    by_slug = {SECTION_SLUG[ch["title"]]: ch for ch in report["chapters"]}
    for slug, n in want.items():
        got = by_slug[slug]["printed_count"]
        if got != n:
            raise SystemExit(f"{book['id']} {slug}: expected {n}, got {got}")


def render_key_chip(doc, spec: dict, dest: Path) -> Path:
    page = doc[spec["page"] - 1]
    y0 = max(page.rect.y0 + 6, float(spec["y0"]) - 6)
    y1 = min(page.rect.y1 - 20, float(spec["y0"]) + 38)
    clip = pymupdf.Rect(page.rect.x0, y0, min(page.rect.x0 + 150, page.rect.x1), y1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    scale = pymupdf.Matrix(DPI / 72, DPI / 72)
    page.get_pixmap(matrix=scale, clip=clip, alpha=False).save(str(dest))
    return dest


def crop_rect(page, spec: dict) -> pymupdf.Rect:
    y0 = max(page.rect.y0 + 6, float(spec["y0"]) - 8)
    if spec.get("clip_y1") is not None:
        y1 = max(float(spec["clip_y1"]), y0 + 40)
    else:
        y1 = page.rect.y1 - 28
    return pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)


WATERMARK_COVERAGE = 0.85
MIN_FIGURE_PT = 24


def figure_hits(doc, spec: dict) -> list[tuple[float, float, int]]:
    """Every sketch xref in the crop, reading order (top then left). Never largest-only."""
    pages = [(spec["page"], spec)]
    cont = spec.get("continuation")
    if spec.get("continues") and cont:
        pages.append((cont["page"], None))
    found: list[tuple[float, float, int]] = []
    seen: set[int] = set()
    for page_no, local in pages:
        page = doc[page_no - 1]
        pw, ph = page.rect.width, page.rect.height
        clip = crop_rect(page, local) if local else pymupdf.Rect(
            page.rect.x0, page.rect.y0 + 40, page.rect.x1,
            float(cont.get("cut_y") or page.rect.y0 + 220) - 4,
        )
        page_hits: list[tuple[float, float, int]] = []
        for info in page.get_image_info(xrefs=True):
            bbox = pymupdf.Rect(info["bbox"])
            w, h = bbox.width, bbox.height
            if w > WATERMARK_COVERAGE * pw and h > WATERMARK_COVERAGE * ph:
                continue
            hit = bbox & clip
            if hit.is_empty or hit.width < MIN_FIGURE_PT or hit.height < MIN_FIGURE_PT:
                continue
            if bbox.y1 < 70:
                continue
            xref = int(info["xref"])
            if xref in seen:
                continue
            seen.add(xref)
            page_hits.append((bbox.y0, bbox.x0, xref))
        page_hits.sort()
        found.extend(page_hits)
    return found


def save_xref_png(doc, xref: int, dest: Path) -> None:
    pix = pymupdf.Pixmap(doc, xref)
    if pix.n - pix.alpha > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(dest))


def extract_figures(doc, spec: dict, dest_dir: Path, key_stem: str) -> list[Path]:
    """Write `{key_stem}_1.png`, `_2`, … one PDF image object per printed sketch."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, (_y, _x, xref) in enumerate(figure_hits(doc, spec), start=1):
        dest = dest_dir / f"{key_stem}_{i}.png"
        save_xref_png(doc, xref, dest)
        paths.append(dest)
    return paths


def extract_figure(doc, spec: dict, dest: Path) -> bool:
    """Pull every PDF image *object* in the crop. Never a page screenshot."""
    stem = dest.stem
    m = re.search(r"^(.*)_(\d+)$", stem)
    key_stem = m.group(1) if m else stem
    return bool(extract_figures(doc, spec, dest.parent, key_stem))


def render_book(book: dict, report: dict) -> None:
    dest = book["out"] / "crops"
    dest.mkdir(parents=True, exist_ok=True)
    figs = book["out"] / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    for ch in report["chapters"]:
        slug = SECTION_SLUG[ch["title"]]
        for spec in ch["crop_plan"]:
            pdf_q = int(spec["q_no"])
            render_crop(doc, spec, dest / f"{slug}_q{pdf_q:02d}.png")
            render_key_chip(doc, spec, dest / f"{slug}_q{pdf_q:02d}_key.png")
            extract_figure(doc, spec, figs / f"{fig_key(book['id'], slug, pdf_q)}.png")
            print(
                f"  crop {book['id']} {slug} Q{pdf_q:02d} continues={spec['continues']}",
                flush=True,
            )
    doc.close()


def fetch_rows(sb, chapter_id: int | None = None) -> dict[tuple[str, str, int], dict]:
    ids = [chapter_id] if chapter_id is not None else [
        p.resolve_chapter_id(sb, no, SUBJECT) for no in CHAPTER_NOS.values()
    ]
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,exam_shift,source_bbox,review_status,"
            "body,solution_md,format,correct_option,numerical_answer"
        )
        .in_("chapter_id", ids)
        .in_("review_status", ["auto_ok", "human_ok"])
        .execute()
        .data
        or []
    )
    out: dict[tuple[str, str, int], dict] = {}
    for row in rows:
        bbox = row.get("source_bbox") or {}
        booklet = str(bbox.get("booklet") or "")
        pdf_q = bbox.get("pdf_q")
        if booklet not in {"2025-jan", "2025-apr"} or pdf_q is None:
            continue
        out[(booklet, section_of(bbox), int(pdf_q))] = row
    return out


def official_key(row: dict) -> tuple[str, str]:
    if str(row.get("format") or "") == "numerical":
        return "numerical", str(row.get("numerical_answer") or "").strip()
    return "mcq", str(row.get("correct_option") or "").strip()


def build_jobs(book: dict, report: dict, db_rows: dict) -> list[dict]:
    (book["out"] / "ocr").mkdir(parents=True, exist_ok=True)
    jobs = []
    for ch in report["chapters"]:
        slug = SECTION_SLUG[ch["title"]]
        keys = {int(k): str(v) for k, v in ch["keys"].items()}
        for spec in ch["crop_plan"]:
            pdf_q = int(spec["q_no"])
            row = db_rows.get((book["id"], slug, pdf_q))
            kind, key = official_key(row) if row else (
                "mcq" if keys.get(pdf_q) in {"1", "2", "3", "4"} else "numerical",
                keys.get(pdf_q, ""),
            )
            jobs.append({
                "booklet": book["id"],
                "section": slug,
                "pdf_q": pdf_q,
                "fig_key": fig_key(book["id"], slug, pdf_q),
                "crop": book["out"] / "crops" / f"{slug}_q{pdf_q:02d}.png",
                "key_png": book["out"] / "crops" / f"{slug}_q{pdf_q:02d}_key.png",
                "fig_png": book["out"] / "figures" / f"{fig_key(book['id'], slug, pdf_q)}.png",
                "cache": book["out"] / "ocr" / f"{slug}_q{pdf_q:02d}.json",
                "kind": kind,
                "pdf_key": key or keys.get(pdf_q, ""),
                "row_id": None if row is None else row["id"],
                "db_q": None if row is None else row["q_no"],
            })
    return jobs


def escape_newlines_in_json_strings(text: str) -> str:
    out: list[str] = []
    in_str = False
    esc = False
    for ch in text:
        if not in_str:
            out.append(ch)
            if ch == '"':
                in_str = True
            continue
        if esc:
            out.append(ch)
            esc = False
            continue
        if ch == "\\":
            out.append(ch)
            esc = True
            continue
        if ch == '"':
            out.append(ch)
            in_str = False
            continue
        if ch == "\n":
            out.append("\\n")
            continue
        if ch == "\r":
            continue
        out.append(ch)
    return "".join(out)


def ocr_json(messages: list, env: dict, limiter: p.RateLimiter) -> dict:
    raw = p.call_sarvam_v2(
        VISION_MODEL, messages, env["SARVAM_API_KEY"], limiter,
        max_tokens=8192, json_object=True,
    )
    try:
        return p.parse_json_content(raw)
    except json.JSONDecodeError:
        text = p.chat_content(raw).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        blob = escape_newlines_in_json_strings(p.salvage_tex_json(text))
        start, end = blob.find("{"), blob.rfind("}")
        if start >= 0 and end > start:
            blob = blob[start:end + 1]
        return json.loads(blob)


def ocr_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = job["cache"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["_cached"] = True
        return data
    assert_model_may_see_image(VISION_MODEL)
    prompt = (
        f"Transcribe ONLY the printed solution for {job['booklet']} {job['section']} "
        f"Q{job['pdf_q']} from image 1. Official key is ({job['pdf_key']}), type {job['kind']}. "
        "Do not copy the listing header Qn. (key). Text first: every printed label and formula. "
        "Never skip a continued-equals line under the first formula (example: $= (x-4)x(x-5)$). "
        f"If and only if there is a graph/sketch, insert [[fig:{job['fig_key']}]] on its own line. "
        "Never attach the whole page as a figure. Never copy watermarks."
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
    raise RuntimeError(f"{job['booklet']} {job['section']} Q{job['pdf_q']}: {last_err}")


def run_ocr(jobs: list[dict], env: dict) -> list[dict]:
    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} OCR jobs in parallel | model={VISION_MODEL}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(ocr_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            label = f"{job['booklet']} {job['section']} Q{job['pdf_q']}"
            try:
                data = fut.result()
                results.append({"ok": True, "job": job, "data": data})
                tag = "cached" if data.get("_cached") else "ok"
                print(f"  [{tag}] {label}", flush=True)
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
                label = f"{job['booklet']} {job['section']} Q{job['pdf_q']}"
                try:
                    data = fut.result()
                    prev["ok"] = True
                    prev["data"] = data
                    prev.pop("error", None)
                    print(f"  [retry-ok] {label}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] {label} {exc}", flush=True)
    return results


ENV_OPEN = re.compile(r"\\begin\{(cases|array|aligned|pmatrix)\}")
ENV_CLOSE = re.compile(r"\\end\{(cases|array|aligned|pmatrix)\}")
NAKED_TEX = re.compile(r"\\(frac|sqrt|int|lambda|Rightarrow|therefore|begin|end)\b")


def join_split_envs(md: str) -> str:
    """Keep a printed cases/array block as one math span, with a row break per printed line."""
    out: list[str] = []
    buf: list[str] | None = None
    for line in (md or "").splitlines():
        if buf is None:
            if ENV_OPEN.search(line) and not ENV_CLOSE.search(line):
                buf = [line]
            else:
                out.append(line)
            continue
        buf.append(line)
        if ENV_CLOSE.search(line):
            parts = [bit.strip().strip("$").strip() for bit in buf]
            joined = parts[0]
            for part in parts[1:]:
                if re.search(r"\\\\\s*$", joined):
                    joined = f"{joined} {part}"
                else:
                    joined = f"{joined} \\\\ {part}"
            out.append(f"${joined}$")
            buf = None
    if buf:
        out.extend(buf)
    return "\n".join(out)


def wrap_naked_tex_lines(md: str) -> str:
    out = []
    for line in (md or "").splitlines():
        stripped = line.strip()
        if stripped and "$" not in stripped and NAKED_TEX.search(stripped):
            out.append(f"${stripped}$")
        else:
            out.append(line)
    return "\n".join(out)


def repair_array_blocks(md: str) -> str:
    def fix(match: re.Match) -> str:
        body = match.group(1)
        bits = re.split(r"\\hline", body)
        head = bits[0]
        rows = [bit.strip() for bit in bits[1:] if bit.strip()]
        if not rows:
            return match.group(0)
        joined = head + r"\hline " + r" \\ \hline ".join(rows)
        return r"\begin{array}" + joined + r"\end{array}"

    return re.sub(r"\\begin\{array\}(.*?)\\end\{array\}", fix, md or "", flags=re.S)


def replace_bare_ampersands(md: str) -> str:
    def fix(match: re.Match) -> str:
        inner = match.group(1)
        if re.search(
            r"\\begin\{(array|cases|aligned|align|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|gathered|split)\}",
            inner,
        ):
            return match.group(0)
        if "&" not in inner:
            return match.group(0)
        return f"${inner.replace('&', r' \text{ and } ')}$"

    return re.sub(r"\$([^$]+)\$", fix, md or "")


UNICODE_TEX = (
    ("∫", r"\int "),
    ("∴", r"\therefore "),
    ("⇒", r"\Rightarrow "),
    ("→", r"\to "),
    ("−", "-"),
)


def replace_unicode_tex(md: str) -> str:
    out = md or ""
    for src, dst in UNICODE_TEX:
        out = out.replace(src, dst)
    return out


def tidy_paper(md: str) -> str:
    body = RUN_TITLE.sub("", md or "")
    body = re.sub(r"(?:\\textstyle)+", "", body)
    body = join_split_envs(body)
    body = repair_array_blocks(body)
    body = replace_bare_ampersands(body)
    body = replace_unicode_tex(body)
    body = wrap_naked_tex_lines(body)
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


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
        raw_md = str(data.get("markdown") or data.get("text") or "").strip()
        if not raw_md:
            hold = "empty_markdown"
        else:
            has_diagram = bool(data.get("has_diagram")) or has_fig
            if has_fig and not ANY_FIG.search(raw_md):
                raw_md = f"[[fig:{job['fig_key']}]]\n{raw_md}"
            if not has_fig:
                has_diagram = False
            md = tidy_paper(assemble_solution_md(job["pdf_q"], raw_md, has_diagram=has_diagram))
            if not ocr_matches_key(answer, md, job["kind"], job["pdf_key"]):
                hold = f"key_mismatch ocr={answer!r} pdf={job['pdf_key']}"
            elif not katex_render_ok(md):
                hold = "katex_render"
    return {
        "booklet": job["booklet"],
        "section": job["section"],
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


def upload_one_figure(sb, pkt: dict, env: dict, books: dict) -> dict | None:
    book = books[pkt["booklet"]]
    local = book["out"] / "figures" / f"{pkt['fig_key']}.png"
    if not local.exists():
        pkt["solution_md"] = ANY_FIG.sub("", pkt["solution_md"] or "")
        print(f"  skip figure {pkt['booklet']} {pkt['section']} Q{pkt['pdf_q']}", flush=True)
        return None
    object_name = f"{FIGURE_PREFIX}/{pkt['fig_key']}.png"
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
        pkt["solution_md"] = ANY_FIG.sub("", pkt["solution_md"] or "")
        print(f"  skip figure {pkt['fig_key']} upload {last_err}", flush=True)
        return None
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    url = f"{base}/storage/v1/object/public/{p.BUCKET}/{object_name}"
    r = httpx.get(url, timeout=30.0)
    if r.status_code != 200:
        pkt["solution_md"] = ANY_FIG.sub("", pkt["solution_md"] or "")
        print(f"  skip figure {pkt['fig_key']} GET {r.status_code}", flush=True)
        return None
    print(f"  storage {pkt['fig_key']} GET {r.status_code}", flush=True)
    return {"figure_key": pkt["fig_key"], "url": url, "bytes": local.stat().st_size}


def upload_figures(sb, packets: list[dict], env: dict, books: dict) -> None:
    jobs = [
        pkt for pkt in packets
        if not pkt["hold"] and ANY_FIG.search(pkt.get("solution_md") or "")
    ]
    uploaded = []
    if not jobs:
        dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions") / "figure_uploads.json", uploaded)
        return
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futs = [pool.submit(upload_one_figure, sb, pkt, env, books) for pkt in jobs]
        for fut in as_completed(futs):
            rec = fut.result()
            if rec:
                uploaded.append(rec)
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions") / "figure_uploads.json", uploaded)


def publish_packets(sb, packets: list[dict]) -> dict:
    live = 0
    holds = []
    written = []
    for pkt in sorted(packets, key=lambda x: (x["booklet"], x["section"], x["pdf_q"])):
        if pkt["hold"] or not pkt.get("solution_md"):
            holds.append({
                "booklet": pkt["booklet"],
                "section": pkt["section"],
                "pdf_q": pkt["pdf_q"],
                "db_q": pkt.get("db_q"),
                "reason": pkt["hold"] or "empty",
            })
            print(
                f"  [hold] {pkt['booklet']} {pkt['section']} Q{pkt['pdf_q']} {pkt['hold']}",
                flush=True,
            )
            continue
        sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq(
            "id", pkt["row_id"]
        ).execute()
        live += 1
        written.append({
            "booklet": pkt["booklet"],
            "section": pkt["section"],
            "pdf_q": pkt["pdf_q"],
            "db_q": pkt["db_q"],
            "id": pkt["row_id"],
        })
        print(
            f"  [paper] {pkt['booklet']} {pkt['section']} Q{pkt['pdf_q']} db={pkt['db_q']}",
            flush=True,
        )
    summary = {"written": live, "holds": holds, "rows": written, "total": len(packets)}
    dump(Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions") / "publish.json", summary)
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
    root = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
    root.mkdir(parents=True, exist_ok=True)

    reports = {}
    all_jobs = []
    for book in BOOKS:
        book["out"].mkdir(parents=True, exist_ok=True)
        report = inventory_chapterwise_solutions(book["pdf"], TITLES)
        dump(book["out"] / "inventory.json", slim_report(report))
        gate_book(book, report)
        reports[book["id"]] = report

    if args.inventory_only:
        return 0

    env = p.load_env()
    sb = p.supabase_client()
    db_rows = fetch_rows(sb)
    print(f"db live 2025 rows matched {len(db_rows)}", flush=True)

    if not args.publish_only:
        for book in BOOKS:
            render_book(book, reports[book["id"]])
            jobs = build_jobs(book, reports[book["id"]], db_rows)
            missing = [j for j in jobs if not j["crop"].exists() or not j["key_png"].exists()]
            if missing:
                raise SystemExit(
                    f"missing crops: {[(j['section'], j['pdf_q']) for j in missing]}"
                )
            dump(book["out"] / "jobs.json", [
                {k: str(v) if isinstance(v, Path) else v for k, v in j.items()}
                for j in jobs
            ])
            all_jobs.extend(jobs)
        results = run_ocr(all_jobs, env)
        by_book = {book["id"]: [] for book in BOOKS}
        packets = []
        for item in results:
            pkt = packet_for(item)
            packets.append(pkt)
            by_book[item["job"]["booklet"]].append({
                "pdf_q": item["job"]["pdf_q"],
                "section": item["job"]["section"],
                "ok": item.get("ok"),
                "error": item.get("error"),
                "cached": (item.get("data") or {}).get("_cached"),
            })
        for book in BOOKS:
            dump(book["out"] / "ocr_results.json", by_book[book["id"]])
            dump(book["out"] / "packets.json", [
                p_ for p_ in packets if p_["booklet"] == book["id"]
            ])
        dump(root / "packets.json", packets)
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
