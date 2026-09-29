#!/usr/bin/env python3
"""Phase 5 / 6 - constrained extraction of the Laws of Motion pages.

    python extract_pass.py --pass 1 --models gemma4,gemini-flash-lite
    python extract_pass.py --pass 2 --models gemini-flash-lite,gemma4
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import pyq_common as p
from bakeoff import (SYSTEM_PROMPT, content_of, page_image_b64, page_slice,
                     user_prompt)


def call_model(model, page_no, slice_, env, limiter):
    if model.startswith("gemini"):
        parts = [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt(page_no, slice_)},
                 {"inline_data": {"mime_type": "image/png",
                                  "data": page_image_b64(page_no)}}]
        return p.call_gemini(model, parts, env["GEMINI_API_KEY"])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "text", "text": user_prompt(page_no, slice_)},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{page_image_b64(page_no)}"}},
        ]},
    ]
    return p.call_sarvam(model, messages, env["SARVAM_API_KEY"], limiter)


def extract_page(page_no, skeleton, models, env, limiter, out_dir):
    slice_ = page_slice(skeleton, page_no)
    allowed_q = {s["q_no"] for s in slice_}
    allowed_f = {k for s in slice_ for k in s["figure_keys"]}
    raw_path = out_dir / f"page_{page_no:03d}.json"

    # A page already on disk is never re-billed.
    if raw_path.exists():
        try:
            payload = json.loads(content_of(json.loads(
                raw_path.read_text(encoding="utf-8"))))
            return page_no, p.validate_page_response(payload, allowed_q, allowed_f), None
        except Exception:
            pass

    last = None
    for attempt, model in enumerate(models, start=1):
        try:
            raw = call_model(model, page_no, slice_, env, limiter)
            payload = json.loads(content_of(raw))
            questions = p.validate_page_response(payload, allowed_q, allowed_f)
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1),
                                encoding="utf-8")
            print(f"page {page_no} ok via {model} (attempt {attempt})")
            return page_no, questions, None
        except Exception as exc:
            last = f"{model}: {type(exc).__name__}: {exc}"
            print(f"page {page_no} attempt {attempt} with {model} failed - {last}")
    return page_no, None, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="pass_no", required=True, choices=["1", "2"])
    ap.add_argument("--models", required=True,
                    help="comma-separated, in escalation order; index 0 is the primary")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()

    env = p.load_env()
    skeleton = p.load_skeleton()
    limiter = p.RateLimiter(60)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    out_dir = p.OUT / "extracted" / f"pass{args.pass_no}"
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted({r["page"] for r in skeleton if r["chapter_no"] == p.CHAPTER_5})
    print(f"pages to extract : {len(pages)} -> {pages}")

    parsed, failures = {}, {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(extract_page, n, skeleton, models, env, limiter, out_dir)
                   for n in pages]
        for fut in futures:
            page_no, questions, err = fut.result()
            if questions is None:
                failures[str(page_no)] = err
                continue
            for q in questions:
                parsed[str(q["q_no"])] = {"body": q["body"],
                                          "options": q.get("options"),
                                          "page": page_no}

    (out_dir / "parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "failures.json").write_text(json.dumps(failures, indent=2),
                                           encoding="utf-8")

    expected = {str(r["q_no"]) for r in skeleton if r["chapter_no"] == p.CHAPTER_5}
    print(f"pages ok     : {len(pages) - len(failures)}/{len(pages)}")
    print(f"questions    : {len(parsed)}/{len(expected)}")
    print(f"missing q_no : {sorted(int(x) for x in expected - set(parsed))}")
    print(f"failed pages : {sorted(int(x) for x in failures)}")


if __name__ == "__main__":
    main()
