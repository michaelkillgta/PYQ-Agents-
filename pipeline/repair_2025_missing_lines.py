#!/usr/bin/env python3
"""Vision pass: every 2025 printed crop vs live transcription. Insert only missing lines.

gemma4 only. Never glm. Parallel. Then re-partition affected packets.
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import VISION_MODEL, assert_model_may_see_image
from ingest_math_2025_paper_solutions import ANY_FIG, BOOKS, fetch_rows, section_of
from ingest_math_2026_jan_di_solutions import PAPER_MARKER, dump
from layout_math_2025_paper_steps import layout_one
from layout_math_2026_jan_di_steps import paper_lines
from run_chapter_agents import v2_json

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
JUNK = re.compile(
    r"mathongo|paperphodna|chapter[- ]wise|jee main 2025|area under curves|"
    r"definite integration|differential equations",
    re.I,
)
KEY_ONLY = re.compile(r"^\$?\(?\s*[1-4]\s*\)?\$?$")
SYSTEM = """You compare a printed JEE Main worked-solution crop to a numbered transcription.
Return JSON only:
{"missing":[{"after_index": int, "latex": string}]}

after_index is the transcription line number the missing printed line should follow.
Use 0 if it belongs at the top (after dropping the listing header 7. / Q7.).

Rules:
- Report a line only if those printed letters are absent from the transcription.
- latex is one printed line as KaTeX markdown ($...$ for formulas, English for labels).
- Do not rewrite, paraphrase, or drop existing transcription lines.
- Do not report watermarks, MathonGo, page titles, or the listing header n. (key).
- Do not report the official option number sitting alone like (4).
- Continued-equals lines MUST be reported if missing, e.g. $= (x-4)x(x-5)$.
- If the transcription already has that content (spacing may differ), omit it.
- If nothing is missing: {"missing":[]}
"""

# Printed January DI Q7 factorization — OCR dropped it.
SEED = {
    ("2025-jan", "di", 7): [{
        "after_index": 1,
        "latex": "$= (x-4)x(x-5)$",
        "source": "seed",
    }],
}


def skeleton(s: str) -> str:
    s = (s or "").lower().replace("−", "-").replace("–", "-").replace("×", "x")
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = ANY_FIG.sub("", s)
    return re.sub(r"[^a-z0-9=+\-()]", "", s)


def keep(latex: str, hay: str) -> bool:
    t = (latex or "").strip()
    if not t or JUNK.search(t) or KEY_ONLY.fullmatch(t):
        return False
    if t.startswith("[[fig:"):
        return False
    sk = skeleton(t)
    if len(sk) < 4:
        return False
    return sk not in hay


def ask_missing(job: dict, env: dict, limiter: p.RateLimiter) -> list[dict]:
    cache: Path = job["miss_cache"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        return list(data.get("missing") or [])
    assert_model_may_see_image(VISION_MODEL)
    numbered = "\n".join(f"{i}. {line}" for i, line in enumerate(job["lines"], start=1))
    prompt = (
        f"{job['label']}. Official key ({job['pdf_key']}). "
        "Image 1 is the printed write-up. Numbered transcription:\n\n"
        + numbered
    )
    messages = [{"role": "system", "content": SYSTEM}]
    messages.extend(p.page_image_message(job["crop"], prompt))
    last_err = None
    for _ in range(3):
        try:
            data = v2_json(VISION_MODEL, messages, env, limiter)
            miss = list(data.get("missing") or [])
            dump(cache, {"missing": miss, "_model": VISION_MODEL})
            return miss
        except Exception as exc:
            last_err = exc
    print(f"  vision fail {job['label']} {last_err}", flush=True)
    return []


def insert_missing(lines: list[str], missing: list[dict]) -> list[str]:
    hay = skeleton("\n".join(lines))
    out = list(lines)
    applied = []
    for rec in missing:
        latex = str(rec.get("latex") or "").strip()
        if not keep(latex, hay):
            continue
        try:
            after = int(rec.get("after_index") or 0)
        except (TypeError, ValueError):
            after = 0
        after = max(0, min(after, len(out)))
        out.insert(after, latex)
        hay = skeleton("\n".join(out))
        applied.append({"after_index": after, "latex": latex, "source": rec.get("source") or "vision"})
    return out, applied


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, 17, "Mathematics")
    rows = fetch_rows(sb, chapter_id)
    jobs = []
    for row in rows.values():
        bbox = row.get("source_bbox") or {}
        booklet = str(bbox.get("booklet") or "")
        pdf_q = int(bbox.get("pdf_q"))
        section = section_of(bbox)
        md = row.get("solution_md") or ""
        if "paper-ocr" not in md:
            continue
        lines = paper_lines(md)
        book = next(b for b in BOOKS if b["id"] == booklet)
        miss_dir = book["out"] / "miss_audit"
        miss_dir.mkdir(parents=True, exist_ok=True)
        key = (
            str(row.get("numerical_answer") or "").strip()
            if str(row.get("format") or "") == "numerical"
            else str(row.get("correct_option") or "").strip()
        )
        jobs.append({
            "booklet": booklet,
            "section": section,
            "pdf_q": pdf_q,
            "id": row["id"],
            "pdf_key": key,
            "label": f"{booklet} {section} Q{pdf_q}",
            "lines": lines,
            "crop": book["out"] / "crops" / f"{section}_q{pdf_q:02d}.png",
            "miss_cache": miss_dir / f"{section}_q{pdf_q:02d}.json",
            "cache": book["out"] / "steps" / f"{section}_q{pdf_q:02d}.json",
        })
    missing_crops = [j for j in jobs if not j["crop"].exists()]
    if missing_crops:
        raise SystemExit(f"missing crops {[j['label'] for j in missing_crops]}")
    print(f"{len(jobs)} vision audits in parallel | model={VISION_MODEL}", flush=True)
    limiter = p.RateLimiter(18)
    vision = {}
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(ask_missing, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                vision[job["id"]] = fut.result()
                n = len(vision[job["id"]])
                print(f"  [{'miss' if n else 'ok'}] {job['label']} reported={n}", flush=True)
            except Exception as exc:
                vision[job["id"]] = []
                print(f"  [fail] {job['label']} {exc}", flush=True)

    patched = []
    layout_jobs = []
    for job in jobs:
        seed = list(SEED.get((job["booklet"], job["section"], job["pdf_q"])) or [])
        combined = list(vision.get(job["id"]) or []) + seed
        new_lines, applied = insert_missing(job["lines"], combined)
        if not applied:
            continue
        patched.append({
            "label": job["label"],
            "id": job["id"],
            "applied": applied,
        })
        if job["cache"].exists():
            job["cache"].unlink()
        layout_jobs.append({**job, "lines": new_lines})
        print(
            f"  [patch] {job['label']} +{len(applied)} "
            + " | ".join(a["latex"][:60] for a in applied),
            flush=True,
        )

    dump(ROOT / "missing_line_patches.json", patched)
    print(f"packets with inserts {len(patched)}/{len(jobs)}", flush=True)
    if not layout_jobs:
        return 0

    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(layout_jobs))) as pool:
        futs = [pool.submit(layout_one, job, env, limiter) for job in layout_jobs]
        for fut in as_completed(futs):
            results.append(fut.result())

    live = 0
    for item in results:
        sb.table("pyq_questions").update({"solution_md": item["solution_md"]}).eq(
            "id", item["id"]
        ).execute()
        live += 1
        print(f"  [live] {item['label']}", flush=True)
    dump(ROOT / "missing_line_publish.json", {
        "written": live,
        "labels": [r["label"] for r in results],
    })
    print(f"written {live}/{len(layout_jobs)}", flush=True)
    return 0 if live == len(layout_jobs) else 2


if __name__ == "__main__":
    raise SystemExit(main())
