#!/usr/bin/env python3
"""Transcribe held 3D Geometry crops with glm5.3-flash (vision)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p
from agents.models import TIEBREAK_MODEL
from format_ocr_math import format_ocr_math
from repair_held_pyq import CROP_SYSTEM, adopt_entry
from run_chapter_agents import v2_json

CHAPTER_NO = 33
REPAIR_DIR = Path("out-math/agents/chapter_33/repair")


def transcribe_batch(q_nos: list[int], batch_name: str) -> dict:
    p.configure_book("math")
    env = p.load_env()
    limiter = p.RateLimiter(18)
    specs = {s["q_no"]: s for s in p.load_skeleton() if s.get("chapter_no") == CHAPTER_NO}
    key_book = p.load_answer_key()
    ch_key = key_book.get(str(CHAPTER_NO), {}).get("answers", {})
    out: dict[str, dict] = {}
    for q in q_nos:
        spec = specs[q]
        png = REPAIR_DIR / f"q{q:03d}.png"
        cache = REPAIR_DIR / f"q{q:03d}_flash.json"
        k = ch_key.get(str(q), {})
        raw = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
        if not raw.get("body"):
            figs = spec.get("figure_keys") or []
            text = (
                f"Question Q{q} ({spec['answer_type']}). "
                f"Official paper type is {spec['answer_type']}. "
                f"Figure keys allowed: {json.dumps(figs)}. "
                "Transcribe this one printed JEE Main question only. "
                "Use $...$ KaTeX. Paper-only: no solver talk, no headings, no dates, no page numbers. "
                "If the paper has (1)(2)(3)(4), fill options as four strings. "
                "If the paper has a blank ______, set mcq false and options null. "
                "Keep [[fig:KEY]] tokens if present."
            )
            messages = [{"role": "system", "content": CROP_SYSTEM}]
            messages.extend(p.page_image_message(png, text))
            raw = {}
            for attempt in range(4):
                try:
                    raw = v2_json(TIEBREAK_MODEL, messages, env, limiter)
                    if raw.get("body"):
                        break
                except Exception as exc:
                    raw = {"error": f"{type(exc).__name__}: {exc}"}
                    time.sleep(2 * (attempt + 1))
            if raw.get("body"):
                cache.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
            elif cache.exists():
                cache.unlink()
        entry = adopt_entry(raw, spec) if raw.get("body") else {
            "body": "",
            "options": None,
            "page": spec["page"],
            "error": raw.get("error", "no_body"),
        }
        fmt = "mcq" if spec["answer_type"] == "mcq" and entry.get("options") else "numerical"
        if spec["answer_type"] == "numerical":
            fmt = "numerical"
            entry["options"] = None
        rec = {
            "format": fmt,
            "body": format_ocr_math(entry.get("body") or ""),
            "options": entry.get("options"),
            "correct_option": int(k["value"]) if fmt == "mcq" and str(k.get("value", "")).isdigit() else None,
            "numerical_answer": str(k.get("value")) if fmt == "numerical" else None,
            "page": spec["page"],
            "error": raw.get("error"),
        }
        out[str(q)] = rec
        preview = (rec["body"] or "")[:80].replace("\n", " ")
        print(f"[{batch_name}] Q{q:3d} {fmt:9s} opts={0 if not rec['options'] else len(rec['options'])} {preview}", flush=True)
    dest = Path(f"out-math/agents/chapter_33/transcribe_{batch_name}.json")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{batch_name}] wrote {dest} n={len(out)}", flush=True)
    return out
