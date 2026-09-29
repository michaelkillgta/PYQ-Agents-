#!/usr/bin/env python3
"""Re-extract 2025 paper-solution figures from PDF image xrefs and upload in parallel.

Q4 January DI stays on the vector redraw (s2025j_di_q04_4). Never page screenshots.
"""
from __future__ import annotations

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
from ingest_math_2025_paper_solutions import (
    ANY_FIG,
    BOOKS,
    FIGURE_PREFIX,
    SECTION_SLUG,
    extract_figure,
)

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
KEEP_VECTOR = {("2025-jan", "di", 4)}
FIG_TOKEN = re.compile(r"\[\[fig:(s2025[ja]_[a-z]+_q\d+_\d+)\]\]")


def bump_key(old: str) -> str:
    return re.sub(r"_(\d+)$", lambda m: f"_{int(m.group(1)) + 1}" if m.group(1) != "4" else m.group(0), old, count=1)


def jobs_from_packets() -> list[dict]:
    packets = json.loads((ROOT / "packets.json").read_text(encoding="utf-8"))
    books = {b["id"]: b for b in BOOKS}
    inventories = {
        b["id"]: json.loads((b["out"] / "inventory.json").read_text(encoding="utf-8"))
        for b in BOOKS
    }
    specs = {}
    for book_id, report in inventories.items():
        for ch in report["chapters"]:
            slug = SECTION_SLUG[ch["title"]]
            for spec in ch["crop_plan"]:
                specs[(book_id, slug, int(spec["q_no"]))] = spec
    jobs = []
    for pkt in packets:
        if pkt.get("hold"):
            continue
        key = (pkt["booklet"], pkt["section"], int(pkt["pdf_q"]))
        if key in KEEP_VECTOR:
            continue
        md = pkt.get("solution_md") or ""
        m = FIG_TOKEN.search(md)
        if not m:
            continue
        spec = specs.get(key)
        if spec is None:
            print(f"  no crop spec {key}", flush=True)
            continue
        old_key = m.group(1)
        new_key = bump_key(old_key)
        if new_key == old_key:
            continue
        dest = books[pkt["booklet"]]["out"] / "figures" / f"{new_key}.png"
        jobs.append({
            "pkt": pkt,
            "spec": spec,
            "pdf": str(books[pkt["booklet"]]["pdf"]),
            "dest": dest,
            "old_key": old_key,
            "new_key": new_key,
        })
    return jobs


def extract_one(job: dict) -> dict:
    dest: Path = job["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(job["pdf"])
    try:
        ok = extract_figure(doc, job["spec"], dest)
    finally:
        doc.close()
    pix = pymupdf.Pixmap(dest) if ok and dest.exists() else None
    rec = {
        **{k: job[k] for k in ("old_key", "new_key")},
        "ok": bool(ok and dest.exists()),
        "bytes": dest.stat().st_size if dest.exists() else 0,
        "wh": None if pix is None else [pix.width, pix.height],
        "row_id": job["pkt"]["row_id"],
        "booklet": job["pkt"]["booklet"],
        "section": job["pkt"]["section"],
        "pdf_q": job["pkt"]["pdf_q"],
        "dest": str(dest),
    }
    print(
        f"  xref {job['pkt']['booklet']} {job['pkt']['section']} "
        f"Q{job['pkt']['pdf_q']:02d} {rec['ok']} {rec['wh']} {rec['bytes']}B "
        f"{job['old_key']} -> {job['new_key']}",
        flush=True,
    )
    return rec


def upload_one(sb, env: dict, rec: dict) -> dict:
    dest = Path(rec["dest"])
    object_name = f"{FIGURE_PREFIX}/{rec['new_key']}.png"
    last_err = None
    for attempt in range(3):
        try:
            sb.storage.from_(p.BUCKET).upload(
                object_name,
                dest.read_bytes(),
                {
                    "content-type": mimetypes.guess_type(dest.name)[0] or "image/png",
                    "upsert": "true",
                },
            )
            last_err = None
            break
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    if last_err is not None:
        rec["upload_ok"] = False
        rec["upload_err"] = str(last_err)
        print(f"  upload fail {rec['new_key']} {last_err}", flush=True)
        return rec
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    url = f"{base}/storage/v1/object/public/{p.BUCKET}/{object_name}"
    r = httpx.get(url, timeout=30.0)
    rec["upload_ok"] = r.status_code == 200
    rec["url"] = url
    rec["get"] = r.status_code
    rec["get_bytes"] = len(r.content) if r.status_code == 200 else 0
    print(f"  storage {rec['new_key']} GET {r.status_code} {rec['get_bytes']}B", flush=True)
    return rec


def swap_token(md: str, old: str, new: str) -> str:
    return md.replace(f"[[fig:{old}]]", f"[[fig:{new}]]")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    jobs = jobs_from_packets()
    print(f"jobs {len(jobs)}", flush=True)
    extracted = []
    with ThreadPoolExecutor(max_workers=len(jobs) or 1) as pool:
        futs = [pool.submit(extract_one, job) for job in jobs]
        for fut in as_completed(futs):
            extracted.append(fut.result())
    ok_extract = [r for r in extracted if r["ok"]]
    print(f"extracted {len(ok_extract)}/{len(extracted)}", flush=True)

    env = p.load_env()
    sb = p.supabase_client()
    uploaded = []
    with ThreadPoolExecutor(max_workers=len(ok_extract) or 1) as pool:
        futs = [pool.submit(upload_one, sb, env, rec) for rec in ok_extract]
        for fut in as_completed(futs):
            uploaded.append(fut.result())
    ok_up = [r for r in uploaded if r.get("upload_ok")]
    print(f"uploaded {len(ok_up)}/{len(uploaded)}", flush=True)

    packets_path = ROOT / "packets.json"
    packets = json.loads(packets_path.read_text(encoding="utf-8"))
    by_row = {r["row_id"]: r for r in ok_up}
    for pkt in packets:
        rec = by_row.get(pkt["row_id"])
        if rec is None:
            continue
        pkt["fig_key"] = rec["new_key"]
        pkt["solution_md"] = swap_token(pkt["solution_md"], rec["old_key"], rec["new_key"])
    packets_path.write_text(json.dumps(packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for book in BOOKS:
        dest = book["out"] / "packets.json"
        if dest.exists():
            subset = [p_ for p_ in packets if p_["booklet"] == book["id"]]
            dest.write_text(json.dumps(subset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    live = 0
    for rec in ok_up:
        cur = (
            sb.table("pyq_questions")
            .select("id,solution_md")
            .eq("id", rec["row_id"])
            .execute()
        )
        if not cur.data:
            print(f"  missing row {rec['row_id']}", flush=True)
            continue
        md = cur.data[0]["solution_md"] or ""
        if f"[[fig:{rec['old_key']}]]" not in md and f"[[fig:{rec['new_key']}]]" in md:
            print(f"  already {rec['new_key']}", flush=True)
            continue
        if f"[[fig:{rec['old_key']}]]" not in md:
            print(f"  skip token {rec['old_key']} not in live {rec['row_id']}", flush=True)
            continue
        new_md = swap_token(md, rec["old_key"], rec["new_key"])
        sb.table("pyq_questions").update({"solution_md": new_md}).eq("id", rec["row_id"]).execute()
        live += 1
        print(f"  live {rec['booklet']} {rec['section']} Q{rec['pdf_q']:02d} {rec['new_key']}", flush=True)

    dump = {
        "extracted": len(ok_extract),
        "uploaded": len(ok_up),
        "live": live,
        "kept_vector": ["s2025j_di_q04_4"],
        "rows": uploaded,
    }
    (ROOT / "xref_figure_uploads.json").write_text(
        json.dumps(dump, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"live tokens {live}", flush=True)
    return 0 if len(ok_up) == len(ok_extract) else 2


if __name__ == "__main__":
    raise SystemExit(main())
