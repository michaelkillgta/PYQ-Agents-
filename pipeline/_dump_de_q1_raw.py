"""Dump raw gemma4 JSON for the two DE Q1 crops that fail json.loads."""
from __future__ import annotations

import json
from pathlib import Path

import pyq_common as p
from agents.models import VISION_MODEL, assert_model_may_see_image
from ingest_math_2025_paper_solutions import BOOKS, OCR_SYSTEM, two_image_message


def load_job(booklet: str, section: str, pdf_q: int) -> dict:
    book = next(b for b in BOOKS if b["id"] == booklet)
    jobs = json.loads((book["out"] / "jobs.json").read_text(encoding="utf-8"))
    rec = next(j for j in jobs if j["section"] == section and int(j["pdf_q"]) == pdf_q)
    rec["crop"] = Path(rec["crop"])
    rec["key_png"] = Path(rec["key_png"])
    rec["cache"] = Path(rec["cache"])
    rec["pdf_q"] = int(rec["pdf_q"])
    return rec


def main() -> None:
    env = p.load_env()
    limiter = p.RateLimiter(18)
    assert_model_may_see_image(VISION_MODEL)
    out = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
    for booklet, section, pdf_q in (("2025-jan", "de", 1), ("2025-apr", "de", 1)):
        job = load_job(booklet, section, pdf_q)
        prompt = (
            f"Transcribe ONLY the printed solution for {job['booklet']} {job['section']} "
            f"Q{job['pdf_q']} from image 1. Official key is ({job['pdf_key']}), type {job['kind']}. "
            "JSON strings must escape newlines as \\n and quotes as \\\". "
            "Do not copy the listing header Qn. (key)."
        )
        messages = [{"role": "system", "content": OCR_SYSTEM}]
        messages.extend(two_image_message(job["crop"], job["key_png"], prompt))
        raw = p.call_sarvam_v2(
            VISION_MODEL, messages, env["SARVAM_API_KEY"], limiter,
            max_tokens=8192, json_object=True,
        )
        text = p.chat_content(raw)
        dest = out / f"raw_{booklet}_{section}_q{pdf_q:02d}.txt"
        dest.write_text(text, encoding="utf-8")
        print(booklet, "len", len(text), "head", repr(text[:120]), "file", dest)


if __name__ == "__main__":
    main()
