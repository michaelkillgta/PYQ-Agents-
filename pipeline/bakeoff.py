#!/usr/bin/env python3
"""Phase 4 - bake-off across 6 pages. Scores structure automatically;
LaTeX correctness is scored by human eye on these pages only."""
import base64
import json
import re
import sys

import pyq_common as p

BAKEOFF_PAGES = [21, 8, 103, 57, 58, 50]
FIG_RE = re.compile(r"\[\[fig:([^\]]+)\]\]")

SYSTEM_PROMPT = """You transcribe questions from a printed JEE Main physics book page.
You are given the page image and the exact list of questions on that page.
Your ONLY job is to transcribe. Never invent, merge, split, renumber or drop a question.

Rules:
- Return JSON: {"questions": [{"q_no": int, "body": str, "options": [str, str, str, str] | null}]}
- Return exactly the q_no values supplied, no others, and every one of them.
- body is Markdown with inline LaTeX between single dollar signs.
- For an MCQ, options is exactly four strings in printed order (1,2,3,4).
- For a numerical question, options is null.
- Where a figure belongs, place the placeholder [[fig:KEY]] using ONLY the figure keys
  supplied for that question. Never invent a key.
- Do not include the date tag, the tier heading, the topic heading or the page number.
- Do not solve anything. Do not add explanation."""


def page_slice(skeleton, page_no):
    recs = sorted((r for r in skeleton if r["page"] == page_no),
                  key=lambda r: (r["column"] == "R", r["bbox"][1]))
    return [{"q_no": r["q_no"], "figure_keys": r["figure_keys"], "tier": r["tier"],
             "topic": r["topic"], "exam_date": r["exam_date"],
             "answer_type": r["answer_type"]} for r in recs]


def user_prompt(page_no, slice_):
    return (f"Page {page_no}. Questions on this page, in reading order "
            f"(left column top to bottom, then right column):\n"
            f"{json.dumps(slice_, ensure_ascii=False, indent=1)}\n"
            f"Transcribe every one of them.")


def page_image_b64(page_no):
    return base64.b64encode(
        (p.OUT / "pages" / f"page_{page_no:03d}.png").read_bytes()).decode()


def run_sarvam(model, pages, skeleton, api_key, limiter, out_dir):
    for page_no in pages:
        slice_ = page_slice(skeleton, page_no)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt(page_no, slice_)},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{page_image_b64(page_no)}"}},
            ]},
        ]
        raw = p.call_sarvam(model, messages, api_key, limiter)
        (out_dir / f"page_{page_no:03d}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  sarvam {model} page {page_no} ok")


def run_gemini(model, pages, skeleton, api_key, out_dir):
    for page_no in pages:
        slice_ = page_slice(skeleton, page_no)
        parts = [
            {"text": SYSTEM_PROMPT + "\n\n" + user_prompt(page_no, slice_)},
            {"inline_data": {"mime_type": "image/png", "data": page_image_b64(page_no)}},
        ]
        raw = p.call_gemini(model, parts, api_key)
        (out_dir / f"page_{page_no:03d}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  gemini {model} page {page_no} ok")


def content_of(raw):
    if "choices" in raw:
        return raw["choices"][0]["message"]["content"]
    return raw["candidates"][0]["content"]["parts"][0]["text"]


def score(candidate, pages, skeleton):
    out_dir = p.OUT / "bakeoff" / candidate
    rows = []
    for page_no in pages:
        slice_ = page_slice(skeleton, page_no)
        allowed_q = {s["q_no"] for s in slice_}
        allowed_f = {k for s in slice_ for k in s["figure_keys"]}
        path = out_dir / f"page_{page_no:03d}.json"
        if not path.exists():
            rows.append({"page": page_no, "valid_json": False, "q_no_exact": False,
                         "figures_placed": 0, "figures_expected": len(allowed_f),
                         "error": "no response file"})
            continue
        try:
            payload = json.loads(content_of(json.loads(path.read_text(encoding="utf-8"))))
            questions = p.validate_page_response(payload, allowed_q, allowed_f)
            placed = len(FIG_RE.findall(json.dumps(questions, ensure_ascii=False)))
            rows.append({"page": page_no, "valid_json": True, "q_no_exact": True,
                         "figures_placed": placed, "figures_expected": len(allowed_f),
                         "error": ""})
        except Exception as exc:
            rows.append({"page": page_no, "valid_json": False, "q_no_exact": False,
                         "figures_placed": 0, "figures_expected": len(allowed_f),
                         "error": f"{type(exc).__name__}: {exc}"})
    return rows


def main():
    env = p.load_env()
    skeleton = p.load_skeleton()
    limiter = p.RateLimiter(60)
    candidate = sys.argv[1]          # gemma4 | sarvam_vision | gemini-flash-lite
    out_dir = p.OUT / "bakeoff" / candidate
    out_dir.mkdir(parents=True, exist_ok=True)

    if candidate == "sarvam_vision":
        print("manual candidate - paste dashboard JSON into", out_dir)
    elif candidate.startswith("gemini"):
        run_gemini(candidate, BAKEOFF_PAGES, skeleton, env["GEMINI_API_KEY"], out_dir)
    else:
        run_sarvam(candidate, BAKEOFF_PAGES, skeleton, env["SARVAM_API_KEY"],
                   limiter, out_dir)

    rows = score(candidate, BAKEOFF_PAGES, skeleton)
    (p.OUT / "bakeoff" / f"{candidate}_score.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    ok = sum(1 for r in rows if r["q_no_exact"])
    print(f"{candidate}: {ok}/{len(rows)} pages with an exact q_no match")
    for r in rows:
        print("  ", r)


if __name__ == "__main__":
    main()
