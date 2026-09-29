"""Finish the two remaining DE Q1 paper packets."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pyq_common as p
from agents.katex_check import katex_render_ok
from agents.models import VISION_MODEL, assert_model_may_see_image
from ingest_math_2025_paper_solutions import (
    BOOKS,
    OCR_SYSTEM,
    dump,
    ocr_json,
    packet_for,
    tidy_paper,
    two_image_message,
)
from ingest_math_2026_jan_di_solutions import assemble_solution_md, ocr_matches_key

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
SPAM = re.compile(r"(?:\\textstyle)+")


def load_job(booklet: str, section: str, pdf_q: int) -> dict:
    book = next(b for b in BOOKS if b["id"] == booklet)
    jobs = json.loads((book["out"] / "jobs.json").read_text(encoding="utf-8"))
    rec = next(j for j in jobs if j["section"] == section and int(j["pdf_q"]) == pdf_q)
    rec["crop"] = Path(rec["crop"])
    rec["key_png"] = Path(rec["key_png"])
    rec["fig_png"] = Path(rec["fig_png"])
    rec["cache"] = Path(rec["cache"])
    rec["pdf_q"] = int(rec["pdf_q"])
    return rec


def loads_ocr(text: str) -> dict:
    blob = SPAM.sub("", text)
    blob = p.salvage_tex_json(blob)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        if not re.search(r'"\s*\}\s*$', blob):
            blob = blob.rstrip().rstrip('"') + '" }'
        return json.loads(blob)


def publish_one(sb, job: dict, data: dict) -> bool:
    dump(job["cache"], data)
    pkt = packet_for({"ok": True, "job": job, "data": data})
    print(job["booklet"], job["section"], job["pdf_q"], pkt.get("hold"), flush=True)
    if pkt["hold"] or not pkt.get("solution_md"):
        raw = str(data.get("markdown") or "")
        md = tidy_paper(assemble_solution_md(job["pdf_q"], raw, has_diagram=False))
        print(" katex", katex_render_ok(md), "key", ocr_matches_key(str(data.get("answer") or ""), md, job["kind"], job["pdf_key"]))
        print(md[:500], flush=True)
        return False
    sb.table("pyq_questions").update({"solution_md": pkt["solution_md"]}).eq("id", job["row_id"]).execute()
    print(" published", job["row_id"], flush=True)
    return True


def main() -> int:
    env = p.load_env()
    sb = p.supabase_client()
    ok = 0

    apr_job = load_job("2025-apr", "de", 1)
    apr_text = (ROOT / "raw_2025-apr_de_q01.txt").read_text(encoding="utf-8")
    apr_data = loads_ocr(apr_text)
    apr_data["_model"] = VISION_MODEL
    if publish_one(sb, apr_job, apr_data):
        ok += 1

    jan_job = load_job("2025-jan", "de", 1)
    assert_model_may_see_image(VISION_MODEL)
    limiter = p.RateLimiter(18)
    prompt = (
        f"Transcribe ONLY the printed solution for {jan_job['booklet']} {jan_job['section']} "
        f"Q{jan_job['pdf_q']} from image 1. Official key is ({jan_job['pdf_key']}), type {jan_job['kind']}. "
        "Never write \\textstyle. Never repeat a macro. Keep JSON short. "
        "Do not copy the listing header Qn. (key)."
    )
    messages = [{"role": "system", "content": OCR_SYSTEM}]
    messages.extend(two_image_message(jan_job["crop"], jan_job["key_png"], prompt))
    last_err = None
    for _ in range(3):
        try:
            raw = p.call_sarvam_v2(
                VISION_MODEL, messages, env["SARVAM_API_KEY"], limiter,
                max_tokens=4096, json_object=True,
            )
            text = SPAM.sub("", p.chat_content(raw))
            (ROOT / "raw_2025-jan_de_q01_retry.txt").write_text(text, encoding="utf-8")
            data = loads_ocr(text)
            data["_model"] = VISION_MODEL
            if publish_one(sb, jan_job, data):
                ok += 1
                last_err = None
                break
            last_err = ValueError(f"packet hold after parse, markdown_len={len(str(data.get('markdown') or ''))}")
        except Exception as exc:
            last_err = exc
            print(" jan retry", exc, flush=True)
    if last_err:
        print("jan de Q1 failed", last_err, flush=True)
    print(f"de q1 published {ok}/2", flush=True)
    return 0 if ok == 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())
