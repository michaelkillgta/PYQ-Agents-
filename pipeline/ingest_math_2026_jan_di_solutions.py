#!/usr/bin/env python3
"""Paper OCR for January 2026 Definite Integration NTA write-ups.

Reads the printed keys + numbered solutions from the MathonGo PDF. gemma4 only.
Never glm. Never rewrites stems.

    python ingest_math_2026_jan_di_solutions.py
    python ingest_math_2026_jan_di_solutions.py --inventory-only
    python ingest_math_2026_jan_di_solutions.py --ocr-only
    python ingest_math_2026_jan_di_solutions.py --publish-only
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
import pymupdf

import pyq_common as p
from agents.katex_check import katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from agents.solvers import matches_pdf_key
from format_ocr_math import format_ocr_math, repair_smashed_tex
from ingest_math_2026_jan_definite import BRAND, JEE_SESSION, PDF_KEY
from pyq_ocr_inventory import (
    inventory_session_solutions_pdf,
    normalize_printed_key,
    render_crop,
)
from run_chapter_agents import v2_json

PDF = Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf")
OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-2026-jan-di-solutions")
BOOKLET = "2026-jan"
CHAPTER_NO = 17
SUBJECT = "Mathematics"
FIGURE_PREFIX = "math/figures"
PAPER_MARKER = "<!-- paper-ocr -->"
EXPECT = 14

OCR_SYSTEM = """You transcribe a printed JEE Main worked solution from a crop.
Return JSON only:
{"pdf_q_no": int, "answer": string, "has_diagram": false, "markdown": string}

markdown rules:
- Copy the printed write-up. Prose labels stay English (Applying king, From (1) and (2), By parts, Let …).
- Do NOT copy the listing header "12. (3)" / "14. (64)" — question number and key are already shown in the app.
- Each printed formula on its own line as $...$ KaTeX. Real newlines, never the two characters \\n.
- Keep every bound, GIF [x], boxed final line, and the official key as the last result.
- Never skip a continued-equals line (example: $= (x-4)x(x-5)$ under $f'(x)=\\ldots$).
- Do NOT insert a picture of the whole page. Do NOT use [[fig:…_crop]].
- has_diagram is true only if the crop contains a graph or sketch that is not typeset math.
  Then put [[fig:KEY]] on its own line where that drawing sits. KEY is given in the user prompt.
- No solver talk, no watermarks, no MathonGo, no #PaperPhodnaHai, no page numbers, no invented steps.
Copy the official key into "answer". Do not solve from scratch."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def two_image_message(q_png: Path, key_png: Path, text: str) -> list:
    q_b64 = base64.b64encode(q_png.read_bytes()).decode("ascii")
    k_b64 = base64.b64encode(key_png.read_bytes()).decode("ascii")
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{q_b64}"}},
            {"type": "text", "text": "Official answer-key strip for this question (image 2):"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{k_b64}"}},
        ],
    }]


def fig_key(pdf_q: int) -> str:
    return f"s2026j_q{pdf_q:02d}_1"


CROP_FIG = re.compile(r"\[\[fig:[a-zA-Z0-9_]*_crop\]\]")
ANY_FIG = re.compile(r"\[\[fig:[^\]]+\]\]")


SOLVER_TALK = re.compile(
    r"\(Wait,?[^)]*\)|Wait, the transcription[^\n$]*|"
    r"Correction based on image flow:[^$\n]*|"
    r"\(incorrect transcription[^)]*\)|"
    r"\\text\{\s*\(incorrect[^}]*\)\s*\}",
    re.I,
)


def strip_overlay(text: str) -> str:
    s = JEE_SESSION.sub(" ", text or "")
    s = BRAND.sub(" ", s)
    s = re.sub(r"#\s*PaperPhodnaHai|www\.mathongo\.com|\bmathongo\b", " ", s, flags=re.I)
    s = SOLVER_TALK.sub(" ", s)
    return s


def split_printed_math(md: str) -> str:
    """One printed line per `$...$`. A whole write-up in one dollar pair will not KaTeX."""
    s = (md or "").replace("\\n", "\n")
    s = re.sub(r"\$\$([^$]+)\$\$", r"$\1$", s)
    s = SOLVER_TALK.sub(" ", s)
    dollar = re.compile(r"\$([^$]+)\$", re.S)

    def split_run(m: re.Match) -> str:
        inner = m.group(1).replace(r"\&", " ")
        # Row breaks inside a matrix are not separate printed lines.
        if re.search(r"\\begin\{", inner):
            return f"${inner.strip()}$" if inner.strip() else ""
        parts = re.split(r"(?:\\\\|\n)+", inner)
        cleaned = []
        for part in parts:
            bit = re.sub(r"\\\s*$", "", part).strip()
            bit = re.sub(r"^\s*\\(\s|$)", "", bit).strip()
            if bit:
                cleaned.append(bit)
        if len(cleaned) <= 1:
            return f"${inner.strip()}$" if inner.strip() else ""
        return "\n".join(f"${p}$" for p in cleaned)

    return dollar.sub(split_run, s)


def format_solution_md(md: str) -> str:
    parts = re.split(r"(\[\[fig:[^\]]+\]\]|\$[^$]+\$)", split_printed_math(md or ""))
    out: list[str] = []
    for part in parts:
        if part.startswith("[[fig:"):
            out.append(part)
            continue
        if part.startswith("$") and part.endswith("$") and len(part) >= 2:
            inner = repair_smashed_tex(part[1:-1]).strip()
            inner = re.sub(
                r"\\text\{([^}]*)\}",
                lambda m: r"\text{" + m.group(1).replace("&", " and ") + "}",
                inner,
            )
            out.append(f"${inner}$" if inner else "")
            continue
        bits = re.split(r"(\n{2,})", part)
        for bit in bits:
            if not bit or bit.startswith("\n"):
                out.append(bit)
                continue
            out.append(format_ocr_math(strip_overlay(bit)))
    packed = "".join(out)
    packed = re.sub(r"\n{3,}", "\n\n", packed).strip()
    packed = break_label_from_math(packed)
    packed = strip_printed_listing(packed)
    return packed


LISTING_HEAD = re.compile(
    r"^(?:Q\s*\d{1,2}\.\s*(?:\([^)]+\)\s*)?|\d{1,2}\.\s*\([^)]+\)\s*)"
)
LISTING_KEY_ONLY = re.compile(r"^\(\s*\d+\s*\)\s*")


def strip_printed_listing(text: str) -> str:
    """Drop '12. (3)' / 'Q1. (2)' listing labels; keep the sentence that follows."""
    out: list[str] = []
    for raw in (text or "").splitlines():
        line = LISTING_HEAD.sub("", raw.strip(), count=1).strip()
        if not out:
            line = LISTING_KEY_ONLY.sub("", line, count=1).strip()
        if line:
            out.append(line)
    return "\n".join(out)


def break_label_from_math(text: str) -> str:
    """Keep 'Applying king' on its own line; never split a closing `$`."""
    out: list[str] = []
    in_math = False
    for ch in text or "":
        if ch == "$":
            if not in_math and out and (out[-1].isalnum() or out[-1] in ").:"):
                out.append("\n")
            out.append("$")
            in_math = not in_math
            continue
        out.append(ch)
    return "".join(out)


def assemble_solution_md(pdf_q: int, markdown: str, has_diagram: bool = False) -> str:
    body = re.sub(r"<!--\s*paper-ocr\s*-->", "", markdown or "").strip()
    body = CROP_FIG.sub("", body)
    if not has_diagram:
        body = ANY_FIG.sub("", body)
    body = format_solution_md(body)
    return f"{PAPER_MARKER}\n\n{body}\n"


def crop_key_strip(doc, answers_page: int, compact_bottom: float, dest: Path) -> Path:
    page = doc[answers_page - 1]
    y0 = max(page.rect.y0 + 88, page.rect.y0 + 40)
    y1 = min(page.rect.y1 - 20, max(compact_bottom + 10, y0 + 40))
    clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
    scale = pymupdf.Matrix(200 / 72, 200 / 72)
    dest.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(matrix=scale, clip=clip, alpha=False).save(str(dest))
    return dest


def render_solution_crops(report: dict) -> list[Path]:
    chapter = report["chapters"][0]
    dest_dir = OUT / "crops"
    dest_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    paths = []
    answers_page = report["key_page"]
    compact_bottom = float(chapter.get("compact_bottom") or 160)
    crop_key_strip(doc, answers_page, compact_bottom, dest_dir / "answer_key.png")
    for spec in chapter["crop_plan"]:
        dest = dest_dir / f"sol_q{spec['q_no']:02d}.png"
        render_crop(doc, spec, dest)
        paths.append(dest)
        print(f"crop Q{spec['q_no']:02d} {dest.name} continues={spec['continues']}", flush=True)
    doc.close()
    return paths


def ocr_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache = job["cache"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["_cached"] = True
        return data
    assert_model_may_see_image(VISION_MODEL)
    kind, key = PDF_KEY[job["pdf_q"]]
    prompt = (
        f"Transcribe ONLY the printed solution for PDF Q{job['pdf_q']} from image 1. "
        f"Official key is ({key}), type {kind}. "
        "Text first: every printed label and formula. "
        f"If and only if there is a graph/sketch, insert [[fig:{job['fig_key']}]] on its own line. "
        "Never attach the whole page as a figure. Never copy watermarks."
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
    raise RuntimeError(f"Q{job['pdf_q']}: {last_err}")


def build_jobs(report: dict) -> list[dict]:
    (OUT / "ocr").mkdir(parents=True, exist_ok=True)
    key_png = OUT / "crops" / "answer_key.png"
    jobs = []
    for spec in report["chapters"][0]["crop_plan"]:
        pdf_q = int(spec["q_no"])
        jobs.append({
            "pdf_q": pdf_q,
            "fig_key": fig_key(pdf_q),
            "crop": OUT / "crops" / f"sol_q{pdf_q:02d}.png",
            "key_png": key_png,
            "cache": OUT / "ocr" / f"q_{pdf_q:02d}.json",
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
                print(f"  [{tag}] Q{job['pdf_q']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "job": job, "error": str(exc)})
                print(f"  [fail] Q{job['pdf_q']} {exc}", flush=True)
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
                    print(f"  [retry-ok] Q{prev['job']['pdf_q']}", flush=True)
                except Exception as exc:
                    prev["error"] = str(exc)
                    print(f"  [retry-fail] Q{prev['job']['pdf_q']} {exc}", flush=True)
    return results


def ocr_matches_key(answer: str, markdown: str, kind: str, key: str) -> bool:
    if matches_pdf_key(str(answer or ""), kind, key):
        return True
    boxed = re.findall(r"\\boxed\{([^}]+)\}", markdown or "")
    if boxed and matches_pdf_key(normalize_printed_key(boxed[-1]), kind, key):
        return True
    if kind == "numerical":
        nums = re.findall(r"-?\d+(?:\.\d+)?", str(answer or "").strip())
        return bool(nums) and nums[-1] == str(key).strip()
    return matches_pdf_key(str(answer or ""), kind, key)


def packet_for(item: dict) -> dict:
    job = item["job"]
    pdf_q = job["pdf_q"]
    kind, key = PDF_KEY[pdf_q]
    hold = None
    md = ""
    answer = ""
    if not item.get("ok"):
        hold = item.get("error") or "ocr_fail"
    else:
        data = item.get("data") or {}
        answer = str(data.get("answer") or "").strip()
        raw_md = str(data.get("markdown") or data.get("text") or "").strip()
        if not raw_md:
            hold = "empty_markdown"
        else:
            md = assemble_solution_md(
                pdf_q,
                raw_md,
                has_diagram=bool(data.get("has_diagram")),
            )
            if not ocr_matches_key(answer, md, kind, key):
                hold = f"key_mismatch ocr={answer!r} pdf={key}"
            elif not katex_render_ok(md):
                hold = "katex_render"
    return {
        "pdf_q": pdf_q,
        "fig_key": job["fig_key"],
        "kind": kind,
        "pdf_key": key,
        "ocr_answer": answer,
        "solution_md": None if hold else md,
        "hold": hold,
    }


def fetch_2026_jan_rows(sb, chapter_id: int) -> dict[int, dict]:
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,exam_shift,source_bbox,review_status,"
            "body,solution_md,format,correct_option,numerical_answer"
        )
        .eq("chapter_id", chapter_id)
        .execute()
        .data
        or []
    )
    by_pdf: dict[int, dict] = {}
    dated: list[dict] = []
    for row in rows:
        bbox = row.get("source_bbox") or {}
        if isinstance(bbox, dict) and str(bbox.get("booklet") or "") == BOOKLET:
            pdf_q = bbox.get("pdf_q")
            if pdf_q is not None:
                by_pdf[int(pdf_q)] = row
                continue
        date = str(row.get("exam_date") or "")
        if date.startswith("2026-01"):
            dated.append(row)
    if len(by_pdf) == EXPECT:
        return by_pdf
    if len(dated) == EXPECT:
        dated.sort(key=lambda r: int(r["q_no"]))
        return {i: row for i, row in enumerate(dated, start=1)}
    raise SystemExit(
        f"expected 14 live 2026-jan rows, booklet_map={len(by_pdf)} dated={len(dated)}"
    )


def upload_figures(sb, packets: list[dict], env: dict) -> None:
    """Student-facing rasters only when the printed solution has a real diagram."""
    uploaded = []
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    for pkt in packets:
        if pkt["hold"] or not ANY_FIG.search(pkt.get("solution_md") or ""):
            continue
        key = pkt["fig_key"]
        local = OUT / "figures" / f"{key}.png"
        if not local.exists():
            pkt["solution_md"] = ANY_FIG.sub("", pkt["solution_md"] or "")
            print(f"  skip figure Q{pkt['pdf_q']} (no diagram raster)", flush=True)
            continue
        object_name = f"{FIGURE_PREFIX}/{key}.png"
        sb.storage.from_(p.BUCKET).upload(
            object_name,
            local.read_bytes(),
            {
                "content-type": mimetypes.guess_type(local.name)[0] or "image/png",
                "upsert": "true",
            },
        )
        url = f"{base}/storage/v1/object/public/{p.BUCKET}/{object_name}"
        r = httpx.get(url, timeout=30.0)
        if r.status_code != 200:
            pkt["hold"] = f"storage_get_{r.status_code}"
            pkt["solution_md"] = None
            continue
        uploaded.append({"figure_key": key, "url": url, "bytes": local.stat().st_size})
        print(f"  storage {key} GET {r.status_code}", flush=True)
    dump(OUT / "figure_uploads.json", uploaded)


def publish_packets(sb, chapter_id: int, packets: list[dict]) -> dict:
    rows = fetch_2026_jan_rows(sb, chapter_id)
    for pdf_q, row in sorted(rows.items()):
        sb.table("pyq_questions").update({"solution_md": None}).eq("id", row["id"]).execute()
        print(f"  cleared glm Q{pdf_q} db={row['q_no']} {row['id'][:8]}", flush=True)
    live = 0
    holds = []
    written = []
    for pkt in sorted(packets, key=lambda x: x["pdf_q"]):
        row = rows.get(pkt["pdf_q"])
        if row is None:
            pkt["hold"] = pkt["hold"] or "missing_row"
        if pkt["hold"] or not pkt.get("solution_md"):
            holds.append({
                "pdf_q": pkt["pdf_q"],
                "db_q": None if row is None else row["q_no"],
                "reason": pkt["hold"] or "empty",
                "ocr_answer": pkt.get("ocr_answer"),
                "pdf_key": pkt["pdf_key"],
            })
            print(f"  [hold] Q{pkt['pdf_q']} {pkt['hold']}", flush=True)
            continue
        sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq(
            "id", row["id"]
        ).execute()
        live += 1
        written.append({
            "pdf_q": pkt["pdf_q"],
            "db_q": row["q_no"],
            "id": row["id"],
            "review_status": row["review_status"],
        })
        print(f"  [paper] Q{pkt['pdf_q']} db={row['q_no']}", flush=True)
    summary = {"written": live, "holds": holds, "rows": written}
    dump(OUT / "publish.json", summary)
    return summary


def gate_or_die(report: dict) -> None:
    print(f"inventory printed={report['printed_total']} keys={report['key_total']} "
          f"solutions={report['solution_total']} crops={report['crop_total']} "
          f"gate_ok={report['gate_ok']}", flush=True)
    if not report["gate_ok"]:
        chapter = report["chapters"][0]
        print(f"  printed={chapter['printed']}", flush=True)
        print(f"  keys={sorted(chapter['keys'])}", flush=True)
        print(f"  solutions={chapter.get('solutions')}", flush=True)
        raise SystemExit("inventory gate failed — printed Qs, keys, and solutions must all be 14")
    if report["printed_total"] != EXPECT:
        raise SystemExit(f"expected {EXPECT}, got printed={report['printed_total']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)

    report = inventory_session_solutions_pdf(PDF)
    dump(OUT / "inventory.json", {
        k: v for k, v in report.items() if k != "chapters"
    } | {
        "chapters": [{
            kk: vv for kk, vv in report["chapters"][0].items()
            if kk not in {"printed_questions", "questions"}
        }]
    })
    gate_or_die(report)
    if args.inventory_only:
        return 0

    if not args.publish_only:
        render_solution_crops(report)
        jobs = build_jobs(report)
        missing = [j for j in jobs if not j["crop"].exists()]
        if missing:
            raise SystemExit(f"missing crops: {[j['pdf_q'] for j in missing]}")
        env = p.load_env()
        results = run_ocr(jobs, env)
        dump(OUT / "ocr_results.json", [
            {
                "pdf_q": r["job"]["pdf_q"],
                "ok": r.get("ok"),
                "error": r.get("error"),
                "cached": (r.get("data") or {}).get("_cached"),
            }
            for r in results
        ])
        packets = [packet_for(r) for r in results]
        dump(OUT / "packets.json", packets)
        if args.ocr_only:
            holds = [p for p in packets if p["hold"]]
            print(f"ocr packets {len(packets) - len(holds)}/{EXPECT} holds {len(holds)}", flush=True)
            return 0 if not holds else 2
    else:
        env = p.load_env()
        jobs = build_jobs(report)
        results = []
        for job in jobs:
            cache = job["cache"]
            if not cache.exists():
                results.append({"ok": False, "job": job, "error": "missing_cache"})
                continue
            data = json.loads(cache.read_text(encoding="utf-8"))
            results.append({"ok": True, "job": job, "data": data})
        packets = [packet_for(r) for r in results]
        dump(OUT / "packets.json", packets)

    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    upload_figures(sb, packets, env)
    summary = publish_packets(sb, chapter_id, packets)
    print(f"written {summary['written']}/{EXPECT} holds {len(summary['holds'])}", flush=True)
    for h in summary["holds"]:
        print(f"  hold Q{h['pdf_q']} {h['reason']}", flush=True)
    return 0 if summary["written"] == EXPECT and not summary["holds"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
