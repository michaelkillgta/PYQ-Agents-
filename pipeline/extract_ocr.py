#!/usr/bin/env python3
"""Extract Laws of Motion (or bake-off pages) via Sarvam Document AI + sarvam-105b.

Gemini and Sarvam /v2 chat are not used. Page images are OCRed with
POST /doc-ai/v1/job/digitise, then sarvam-105b (text-only /v1) splits the
OCR into the constrained question JSON. Whitelist still applies.

    python extract_ocr.py --pages 21,8,103,57,58,50 --out bakeoff/sarvam-ocr
    python extract_ocr.py --chapter 5 --out extracted/pass1
"""
import argparse
import json

import pyq_common as p
from bakeoff import page_slice
from parse_ocr_page import parse_digitise_to_questions


def extract_page(page_no, skeleton, env, limiter, out_dir):
    del limiter
    slice_ = page_slice(skeleton, page_no)
    allowed_q = {s["q_no"] for s in slice_}
    allowed_f = {k for s in slice_ for k in s["figure_keys"]}
    raw_path = out_dir / f"page_{page_no:03d}.json"

    try:
        digitise = p.digitise_page(page_no, env["SARVAM_API_KEY"])
        questions = parse_digitise_to_questions(digitise, slice_)
        payload = {"questions": questions}
        p.validate_page_response(payload, allowed_q, allowed_f)
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        print(f"page {page_no} ok  q={len(questions)}")
        return page_no, questions, None
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        print(f"page {page_no} failed - {err}")
        return page_no, None, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", help="comma-separated 1-indexed page numbers")
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--out", required=True, help="directory under out/")
    args = ap.parse_args()

    env = p.load_env()
    skeleton = p.load_skeleton()
    limiter = p.RateLimiter(60)
    out_dir = p.OUT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.pages:
        pages = [int(x) for x in args.pages.split(",") if x.strip()]
    elif args.chapter:
        pages = sorted({r["page"] for r in skeleton if r["chapter_no"] == args.chapter})
    else:
        raise SystemExit("pass --pages or --chapter")

    print(f"pages to extract : {len(pages)} -> {pages}")
    parsed, failures = {}, {}
    for page_no in pages:
        n, questions, err = extract_page(page_no, skeleton, env, limiter, out_dir)
        if questions is None:
            failures[str(n)] = err
            continue
        for q in questions:
            parsed[str(q["q_no"])] = {"body": q["body"],
                                      "options": q.get("options"),
                                      "page": n}

    (out_dir / "parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "failures.json").write_text(json.dumps(failures, indent=2),
                                           encoding="utf-8")
    print(f"pages ok     : {len(pages) - len(failures)}/{len(pages)}")
    print(f"questions    : {len(parsed)}")
    print(f"failed pages : {sorted(int(x) for x in failures)}")


if __name__ == "__main__":
    main()
