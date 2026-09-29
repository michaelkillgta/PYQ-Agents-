#!/usr/bin/env python3
"""Extract every 2024 Apr DI Q1 PDF xref and upload in parallel."""
from __future__ import annotations

import json
import mimetypes
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
import pymupdf

import pyq_common as p
from ingest_math_2024_di_solutions import BOOKS, FIGURE_PREFIX
from ingest_math_2025_paper_solutions import extract_figures

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-2024-apr-di-solutions")
KEY_STEM = "s2024a_q01"
ROW_ID = "f5b3b124-b8ea-45ea-aeb9-0885223ea5d7"

SOLUTION_MD = """<!-- paper-ocr -->

## Step 1: Graphs

[[fig:s2024a_q01_1]]
[[fig:s2024a_q01_2]]
[[fig:s2024a_q01_3]]

## Step 2: Function definition

$h(x)=\\begin{cases} x-2+2-x=0, & 0\\le x\\le 2 \\\\ -x-2+2=-x & -2\\le x<0 \\end{cases}$

## Step 3: Integral evaluation

$\\Rightarrow \\int_{0}^{2} h(x)\\,dx = 0$ and $\\int_{-2}^{0} h(x)\\,dx = 2$
"""


def upload_one(sb, env: dict, local: Path) -> dict:
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
        raise RuntimeError(f"{local.stem}: {last_err}")
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    url = f"{base}/storage/v1/object/public/{p.BUCKET}/{object_name}"
    r = httpx.get(url, timeout=30.0)
    if r.status_code != 200 or r.content != local.read_bytes():
        raise RuntimeError(f"{local.stem}: GET {r.status_code}")
    print(f"  storage {local.stem} {len(r.content)}B", flush=True)
    return {"figure_key": local.stem, "url": url, "bytes": local.stat().st_size}


def main() -> None:
    env = p.load_env()
    sb = p.supabase_client()
    book = next(b for b in BOOKS if b["id"] == "2024-apr")
    inv = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))
    spec = next(s for s in inv["chapters"][0]["crop_plan"] if int(s["q_no"]) == 1)
    dest = OUT / "figures"
    dest.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(book["pdf"])
    try:
        paths = extract_figures(doc, spec, dest, KEY_STEM)
    finally:
        doc.close()
    if len(paths) != 3:
        raise SystemExit(f"expected 3 xrefs, got {len(paths)} {[p.name for p in paths]}")
    with ThreadPoolExecutor(max_workers=len(paths)) as pool:
        futs = [pool.submit(upload_one, sb, env, path) for path in paths]
        recs = [fut.result() for fut in as_completed(futs)]
    sb.table("pyq_questions").update({"solution_md": SOLUTION_MD}).eq("id", ROW_ID).execute()
    packets = json.loads((OUT / "packets.json").read_text(encoding="utf-8"))
    for pkt in packets:
        if int(pkt["pdf_q"]) == 1:
            pkt["solution_md"] = SOLUTION_MD
            pkt["has_figure"] = True
    (OUT / "packets.json").write_text(json.dumps(packets, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"uploaded": recs, "row": ROW_ID}, indent=2), flush=True)


if __name__ == "__main__":
    main()
