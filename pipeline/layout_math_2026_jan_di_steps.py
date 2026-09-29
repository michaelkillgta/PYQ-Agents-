#!/usr/bin/env python3
"""Cut existing 2026 paper OCR into labeled steps. gemma4 text only. No glm. No re-OCR.

Does not rewrite printed lines. Titles are new. Parallel.

    python layout_math_2026_jan_di_steps.py
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyq_common as p
from agents.models import VISION_MODEL
from ingest_math_2026_jan_definite import PDF_KEY
from ingest_math_2026_jan_di_solutions import (
    EXPECT,
    OUT,
    PAPER_MARKER,
    dump,
    fetch_2026_jan_rows,
)
from run_chapter_agents import v2_json

STEPS_DIR = OUT / "steps"
PAPER_HEADING = re.compile(r"^##\s+Step\s+\d+:\s+", re.I)
TITLE_OK = re.compile(r"^[A-Za-z][A-Za-z0-9 /&+'’-]{1,48}$")
LABEL_CUT = re.compile(
    r"^(Applying|Let|By parts|From |Split|Using |Now |Therefore|Thus |Hence )",
    re.I,
)

LAYOUT_SYSTEM = """You only partition a printed JEE solution into steps.
Do not rewrite, paraphrase, drop, or add any solution line.
Return JSON only:
{"steps":[{"title":"short method name","start":1,"end":3}]}
start and end are 1-based inclusive line numbers from the numbered list.
Rules:
- Cover every line exactly once, in order, no gaps, no overlaps.
- 3 to 6 steps when the write-up has that many natural cuts; otherwise as many as needed.
- title is 2-6 words (Decomposition, Symmetry, Substitution, Integration, Final evaluation).
- Titles are new. Lines stay exactly as printed."""


def paper_lines(md: str) -> list[str]:
    body = re.sub(r"<!--\s*paper-ocr\s*-->", "", md or "").strip()
    lines = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or PAPER_HEADING.match(line):
            continue
        lines.append(line)
    return lines


def numbered_list(lines: list[str]) -> str:
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start=1))


def clean_title(raw: str, index: int) -> str:
    t = re.sub(r"^Step\s*\d+\s*:\s*", "", str(raw or ""), flags=re.I).strip()
    t = re.sub(r"\s+", " ", t)
    if not TITLE_OK.match(t):
        t = f"Step {index}"
        return t
    return t


def validate_cuts(n: int, steps: list[dict]) -> list[dict] | None:
    if n <= 0 or not steps:
        return None
    covered: list[int] = []
    out = []
    expected = 1
    for i, rec in enumerate(steps, start=1):
        try:
            start = int(rec.get("start"))
            end = int(rec.get("end"))
        except (TypeError, ValueError):
            return None
        if start != expected or end < start or end > n:
            return None
        out.append({
            "title": clean_title(str(rec.get("title") or ""), i),
            "start": start,
            "end": end,
        })
        covered.extend(range(start, end + 1))
        expected = end + 1
    if covered != list(range(1, n + 1)):
        return None
    return out


def heuristic_cuts(lines: list[str]) -> list[dict]:
    starts = [0]
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if LABEL_CUT.match(line) and not re.fullmatch(r"\$[^$]+\$", line):
            starts.append(i)
    starts.append(len(lines))
    uniq = []
    for s in starts:
        if not uniq or s > uniq[-1]:
            uniq.append(s)
    steps = []
    for i in range(len(uniq) - 1):
        a, b = uniq[i], uniq[i + 1]
        if a >= b:
            continue
        label = lines[a]
        title = label if LABEL_CUT.match(label) and len(label) < 40 and "$" not in label else f"Working {i + 1}"
        steps.append({"title": clean_title(title, i + 1), "start": a + 1, "end": b})
    return validate_cuts(len(lines), steps) or [{
        "title": "Solution",
        "start": 1,
        "end": len(lines),
    }]


def assemble_steps(lines: list[str], cuts: list[dict]) -> str:
    parts = [PAPER_MARKER, ""]
    for i, cut in enumerate(cuts, start=1):
        parts.append(f"## Step {i}: {cut['title']}")
        parts.append("")
        parts.extend(lines[cut["start"] - 1:cut["end"]])
        parts.append("")
    packed = "\n".join(parts).strip() + "\n"
    rebuilt = paper_lines(packed)
    if rebuilt != lines:
        raise ValueError("layout changed printed lines")
    return packed


def ask_cuts(lines: list[str], pdf_q: int, env: dict, limiter: p.RateLimiter) -> list[dict]:
    user = (
        f"PDF Q{pdf_q}. Official key {PDF_KEY[pdf_q][1]}. "
        "Assign every line to a step.\n\n"
        + numbered_list(lines)
    )
    messages = [
        {"role": "system", "content": LAYOUT_SYSTEM},
        {"role": "user", "content": user},
    ]
    last_err = None
    for _ in range(3):
        try:
            data = v2_json(VISION_MODEL, messages, env, limiter)
            cuts = validate_cuts(len(lines), list(data.get("steps") or []))
            if cuts:
                return cuts
            last_err = ValueError("coverage")
        except Exception as exc:
            last_err = exc
    print(f"  Q{pdf_q} gemma cuts failed ({last_err}); heuristic", flush=True)
    return heuristic_cuts(lines)


def layout_one(job: dict, env: dict, limiter: p.RateLimiter) -> dict:
    cache: Path = job["cache"]
    lines: list[str] = job["lines"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        cuts = validate_cuts(len(lines), list(data.get("steps") or []))
        if cuts:
            md = assemble_steps(lines, cuts)
            return {"ok": True, "pdf_q": job["pdf_q"], "solution_md": md, "cached": True, "id": job["id"]}
    cuts = ask_cuts(lines, job["pdf_q"], env, limiter)
    dump(cache, {"pdf_q": job["pdf_q"], "steps": cuts, "_model": VISION_MODEL})
    md = assemble_steps(lines, cuts)
    return {"ok": True, "pdf_q": job["pdf_q"], "solution_md": md, "cached": False, "id": job["id"]}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    STEPS_DIR.mkdir(parents=True, exist_ok=True)
    env = p.load_env()
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, 17, "Mathematics")
    rows = fetch_2026_jan_rows(sb, chapter_id)
    jobs = []
    for pdf_q in range(1, EXPECT + 1):
        row = rows.get(pdf_q)
        if row is None:
            print(f"missing row Q{pdf_q}", flush=True)
            continue
        lines = paper_lines(row.get("solution_md") or "")
        if not lines:
            print(f"empty paper Q{pdf_q}", flush=True)
            continue
        jobs.append({
            "pdf_q": pdf_q,
            "id": row["id"],
            "lines": lines,
            "cache": STEPS_DIR / f"q_{pdf_q:02d}.json",
        })
    if len(jobs) != EXPECT:
        raise SystemExit(f"need {EXPECT} paper packets, got {len(jobs)}")

    limiter = p.RateLimiter(18)
    print(f"{len(jobs)} layout jobs in parallel | model={VISION_MODEL} | text only", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(layout_one, job, env, limiter): job for job in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                item = fut.result()
                results.append(item)
                tag = "cached" if item.get("cached") else "ok"
                print(f"  [{tag}] Q{job['pdf_q']}", flush=True)
            except Exception as exc:
                results.append({"ok": False, "pdf_q": job["pdf_q"], "error": str(exc), "id": job["id"]})
                print(f"  [fail] Q{job['pdf_q']} {exc}", flush=True)

    written = 0
    holds = []
    for item in sorted(results, key=lambda r: int(r["pdf_q"])):
        if not item.get("ok") or not item.get("solution_md"):
            holds.append({"pdf_q": item["pdf_q"], "reason": item.get("error") or "layout"})
            continue
        sb.table("pyq_questions").update({"solution_md": item["solution_md"]}).eq(
            "id", item["id"]
        ).execute()
        written += 1
        print(f"  [steps] Q{item['pdf_q']}", flush=True)
    dump(OUT / "layout_publish.json", {"written": written, "holds": holds})
    print(f"written {written}/{EXPECT} holds {len(holds)}", flush=True)
    return 0 if written == EXPECT and not holds else 2


if __name__ == "__main__":
    raise SystemExit(main())
