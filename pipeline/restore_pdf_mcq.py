#!/usr/bin/env python3
"""Restore PDF-keyed MCQs that were stored as option-less numericals.

Uses glm5.3-flash on a crop. Never changes the PDF option number.

    python restore_pdf_mcq.py
    python restore_pdf_mcq.py --chapter 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.models import TIEBREAK_MODEL
from format_ocr_math import format_ocr_math
from repair_held_pyq import crop_png
from run_chapter_agents import spec_map, v2_json
from write_and_publish import options_publishable

FORCE_MCQ = """You look at one printed JEE Main PYQ crop.
Return JSON only:
{"q_no":int,"mcq":true,"body":str,"options":[str,str,str,str]}
This item is a 4-option MCQ on the paper. Transcribe the stem and (1)(2)(3)(4).
Use $...$ KaTeX. Paper-only: no solver talk, no headings, no dates, no next question.
Keep [[fig:KEY]] if the prompt lists that key."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def transcribe(png: Path, spec: dict, env: dict, limiter: p.RateLimiter) -> dict:
    figs = spec.get("figure_keys") or []
    text = (
        f"Question Q{spec['q_no']} is a 4-option MCQ. "
        f"Figure keys allowed: {json.dumps(figs)}. "
        "Fill options as four strings in printed order."
    )
    messages = [{"role": "system", "content": FORCE_MCQ}]
    messages.extend(p.page_image_message(png, text))
    return v2_json(TIEBREAK_MODEL, messages, env, limiter)


def publish_mcq(sb, qid: str, body: str, options: list[str], pdf_choice: int) -> None:
    sb.table("pyq_questions").update({
        "format": "mcq",
        "body": body,
        "correct_option": pdf_choice,
        "numerical_answer": None,
        "review_status": "human_ok",
        "extraction_confidence": 1.0,
    }).eq("id", qid).execute()
    sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
    sb.table("pyq_question_options").insert([
        {"question_id": qid, "option_index": i, "body": opt}
        for i, opt in enumerate(options, start=1)
    ]).execute()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int)
    args = ap.parse_args()
    p.configure_book("math")
    env = p.load_env()
    limiter = p.RateLimiter(48)
    pdf = Path(p.BOOKS["math"]["pdf"])
    key_book = p.load_answer_key()
    mm = json.loads(Path("out-math/glm_option_audit/pdf_key_vs_db.json").read_text(encoding="utf-8"))
    bleed = [
        {"chapter_no": 9, "q_no": 152, "pdf": "mcq:4"},
        {"chapter_no": 25, "q_no": 38, "pdf": "mcq:2"},
        {"chapter_no": 33, "q_no": 54, "pdf": "mcq:2"},
        {"chapter_no": 33, "q_no": 273, "pdf": "mcq:2"},
    ]
    seen = {(r["chapter_no"], r["q_no"]) for r in mm}
    for extra in bleed:
        if (extra["chapter_no"], extra["q_no"]) not in seen:
            mm.append(extra)
    if args.chapter:
        mm = [r for r in mm if r["chapter_no"] == args.chapter]
    sb = p.supabase_client()
    ok = fail = 0
    for row in mm:
        ch_no = int(row["chapter_no"])
        q_no = int(row["q_no"])
        k = ((key_book.get(str(ch_no)) or {}).get("answers") or {}).get(str(q_no)) or {}
        pdf_choice = int(str(k.get("value") or row.get("pdf", "").split(":")[-1]))
        specs = spec_map(p.load_skeleton(), ch_no)
        spec = specs.get(q_no)
        if not spec:
            print(f"ch{ch_no} Q{q_no} no skeleton", flush=True)
            fail += 1
            continue
        spec = dict(spec)
        spec["answer_type"] = "mcq"
        x0, y0, x1, y1 = spec["bbox"]
        spec["bbox"] = [x0, y0, x1, y1 + 160]
        ch_id = p.resolve_chapter_id(sb, ch_no, "Mathematics")
        qrow = (
            sb.table("pyq_questions")
            .select("id,format,pyq_question_options(option_index)")
            .eq("chapter_id", ch_id)
            .eq("q_no", q_no)
            .limit(1)
            .execute()
            .data
        )
        if not qrow:
            print(f"ch{ch_no} Q{q_no} missing db", flush=True)
            fail += 1
            continue
        qid = qrow[0]["id"]
        n_opts = len(qrow[0].get("pyq_question_options") or [])
        if qrow[0].get("format") == "mcq" and n_opts == 4:
            print(f"ch{ch_no} Q{q_no} already mcq", flush=True)
            ok += 1
            continue
        repair_dir = p.OUT / "agents" / f"chapter_{ch_no}" / "restore_mcq"
        crop = repair_dir / f"q{q_no:03d}_tall.png"
        cache = repair_dir / f"q{q_no:03d}_flash_tall.json"
        try:
            crop_png(pdf, spec, crop, specs)
            if cache.exists():
                raw = json.loads(cache.read_text(encoding="utf-8"))
            else:
                raw = transcribe(crop, spec, env, limiter)
                dump(cache, raw)
        except Exception as exc:
            print(f"ch{ch_no} Q{q_no} crop/vision fail {exc}", flush=True)
            fail += 1
            continue
        body = format_ocr_math(str(raw.get("body") or "").strip())
        options = raw.get("options")
        if is_solver_dump(body) or not options_publishable(options):
            print(f"ch{ch_no} Q{q_no} shape fail body={body[:60]!r}", flush=True)
            fail += 1
            continue
        options = [format_ocr_math(str(t or "")) for t in options]
        if not all(katex_render_ok(t) for t in [body, *options]):
            print(f"ch{ch_no} Q{q_no} katex fail", flush=True)
            fail += 1
            continue
        publish_mcq(sb, qid, body, options, pdf_choice)
        print(f"ch{ch_no} Q{q_no} restored mcq key={pdf_choice}", flush=True)
        ok += 1
    print(f"restored {ok} failed {fail} of {len(mm)}", flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
