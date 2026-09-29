#!/usr/bin/env python3
"""Ingest the Jan 2026 Definite Integration booklet onto catalog_slug definite-integration.

Isolated cache: out-math-2026-jan-di/  — never writes Physics out/ or the 2019–2025 out-math/ book.
PDF keys are ground truth. Duplicates of older-bank questions are allowed.

    python ingest_math_2026_jan_definite.py

DB q_no is 226–239 (PDF Q1–Q14) on Mathematics chapter 19 so a later delete is
`chapter_id=84 AND q_no >= 226`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.coverage import coverage_diff
from agents.katex_check import is_solver_dump
from agents.models import FALLBACK_SOLVERS, PRIMARY_SOLVER
from agents.promotion import final_publish_status
from agents.publish import shape_ok_for, upsert_question
from agents.solvers import solve_match, solver_has_answer
from agents.vision import observer_shape, question_rows, vision_agree
from audit_paper_text import flags_for
from bakeoff import page_slice
from format_ocr_math import format_ocr_math
from parse_ocr_page import parse_digitise_to_questions
from run_chapter_agents import (
    adopt_from_observer,
    observe_page,
    row_audit_ok,
    row_katex_ok,
    solver_answer,
    tiebreak_page,
)

PDF = Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf")
OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-2026-jan-di")
CHAPTER_ID = 84
Q_NO_OFFSET = 225  # PDF Q1 → DB 226
DPI = 200
QUESTION_PAGES = (1, 2)

# PDF answer key (page 3). MCQ values are option indexes 1–4.
PDF_KEY = {
    1: ("numerical", "9"),
    2: ("mcq", "2"),
    3: ("mcq", "3"),
    4: ("numerical", "2"),
    5: ("mcq", "2"),
    6: ("numerical", "36"),
    7: ("mcq", "3"),
    8: ("numerical", "16"),
    9: ("mcq", "4"),
    10: ("numerical", "17"),
    11: ("mcq", "4"),
    12: ("mcq", "3"),
    13: ("numerical", "210"),
    14: ("numerical", "64"),
}

Q_HEAD = re.compile(
    r"^Q(\d+)\.\s*JEE Main 2026\s*\((\d{1,2})\s+January\s+Shift\s+([12])\)\s*$",
    re.I,
)
JEE_SESSION = re.compile(
    r"JEE Main 20\d{2}\s*\(\d{1,2}\s+[A-Za-z]+\s+Shift\s+[12]\)",
    re.I,
)
BRAND = re.compile(
    r"(?:Definite Integration\s*)?Questions with Answer Keys|"
    r"JEE Main 2026 \(January\) Question Bank|"
    r"#\s*PaperPhodnaHai|"
    r"www\.mathongo\.com|"
    r"\bmathongo\b",
    re.I,
)
BLANK_SLOT = re.compile(r"_{3,}")


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def configure_cache() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)
    (OUT / "ocr").mkdir(exist_ok=True)
    (OUT / "agents").mkdir(exist_ok=True)
    p.OUT = OUT
    p.PDF_PATH = str(PDF)
    p.FIGURE_PREFIX = "math/figures"


def rasterize() -> None:
    doc = pymupdf.open(PDF)
    zoom = DPI / 72
    mat = pymupdf.Matrix(zoom, zoom)
    for pno in QUESTION_PAGES:
        pix = doc[pno - 1].get_pixmap(matrix=mat, alpha=False)
        dest = OUT / "pages" / f"page_{pno:03d}.png"
        pix.save(str(dest))
        print(f"raster {dest.name} {pix.width}x{pix.height}", flush=True)
    doc.close()


def build_skeleton() -> list[dict]:
    doc = pymupdf.open(PDF)
    records = []
    for pno in QUESTION_PAGES:
        page = doc[pno - 1]
        pw, ph = page.rect.width, page.rect.height
        anchors = []
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                txt = "".join(s["text"] for s in line["spans"]).strip()
                m = Q_HEAD.match(txt)
                if not m:
                    continue
                q_no = int(m.group(1))
                day = int(m.group(2))
                shift = "evening" if m.group(3) == "2" else "morning"
                x0, y0, x1, y1 = line["bbox"]
                anchors.append({
                    "q_no": q_no,
                    "y": y0,
                    "bbox_line": [x0, y0, x1, y1],
                    "exam_date": f"2026-01-{day:02d}",
                    "exam_shift": shift,
                })
        anchors.sort(key=lambda a: a["y"])
        for i, rec in enumerate(anchors):
            y0 = rec["y"]
            y1 = anchors[i + 1]["y"] if i + 1 < len(anchors) else ph - 48
            kind, value = PDF_KEY[rec["q_no"]]
            records.append({
                "chapter_no": 19,
                "chapter_title": "Definite Integration",
                "topic": "JEE Main 2026 January",
                "tier": "must_do",
                "q_no": rec["q_no"],
                "page": pno,
                "column": "L",
                "bbox": [36.0, round(y0, 1), round(pw - 36, 1), round(y1, 1)],
                "figure_keys": [],
                "exam_date": rec["exam_date"],
                "exam_shift": rec["exam_shift"],
                "out_of_syllabus": False,
                "good_to_solve": False,
                "answer_type": kind,
                "answer_value": value,
                "body": None,
                "options": None,
                "review_status": "skeleton_only",
            })
    doc.close()
    records.sort(key=lambda r: r["q_no"])
    if [r["q_no"] for r in records] != list(range(1, 15)):
        raise SystemExit(f"expected Q1–Q14, got {[r['q_no'] for r in records]}")
    return records


def strip_branding(text: str) -> str:
    s = JEE_SESSION.sub(" ", text or "")
    s = BRAND.sub(" ", s)
    s = BLANK_SLOT.sub(" ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def clean_entry(entry: dict, spec: dict) -> dict:
    body = format_ocr_math(strip_branding(entry.get("body") or ""))
    options = entry.get("options")
    if spec["answer_type"] == "mcq":
        if isinstance(options, list) and len(options) == 4:
            options = [format_ocr_math(strip_branding(o)) for o in options]
        else:
            options = None
    else:
        options = None
    return {"body": body, "options": options, "page": entry.get("page") or spec["page"]}


def seed_rows(sb, skeleton: list[dict]) -> dict[int, str]:
    rows = []
    for rec in skeleton:
        mcq = rec["answer_type"] == "mcq"
        rows.append({
            "chapter_id": CHAPTER_ID,
            "topic_id": None,
            "q_no": Q_NO_OFFSET + rec["q_no"],
            "tier": "must_do",
            "format": "mcq" if mcq else "numerical",
            "body": None,
            "correct_option": int(rec["answer_value"]) if mcq else None,
            "numerical_answer": None if mcq else rec["answer_value"],
            "exam_date": rec["exam_date"],
            "exam_shift": rec["exam_shift"],
            "out_of_syllabus": False,
            "good_to_solve": False,
            "source_page": rec["page"],
            "source_bbox": rec["bbox"],
            "review_status": "skeleton_only",
        })
    sb.table("pyq_questions").upsert(rows, on_conflict="chapter_id,q_no").execute()
    fetched = (
        sb.table("pyq_questions")
        .select("id,q_no")
        .eq("chapter_id", CHAPTER_ID)
        .gte("q_no", Q_NO_OFFSET + 1)
        .lte("q_no", Q_NO_OFFSET + 14)
        .execute()
        .data
    )
    return {int(r["q_no"]) - Q_NO_OFFSET: r["id"] for r in fetched}


def main() -> int:
    if not PDF.is_file():
        raise SystemExit(f"missing PDF {PDF}")
    configure_cache()
    env = p.load_env()
    limiter = p.RateLimiter(60)
    out_dir = OUT / "agents"
    out_dir.mkdir(parents=True, exist_ok=True)

    rasterize()
    skeleton = build_skeleton()
    dump(OUT / "skeleton.json", skeleton)
    dump(OUT / "answer_key.json", {
        "19": {
            "chapter_no": 19,
            "title": "Definite Integration",
            "answers": {
                str(q): {"type": kind, "value": val}
                for q, (kind, val) in PDF_KEY.items()
            },
        }
    })
    specs = {int(r["q_no"]): r for r in skeleton}
    print(f"skeleton {len(skeleton)} questions on pages {QUESTION_PAGES}", flush=True)

    digitise = p.digitise_pages_parallel(list(QUESTION_PAGES), env["SARVAM_API_KEY"], workers=2)
    dump(out_dir / "digitise_failures.json",
         {str(k): v for k, v in digitise.items() if isinstance(v, str)})

    parsed, parse_failures, by_page = {}, {}, {}
    for page_no in QUESTION_PAGES:
        payload = digitise.get(page_no)
        if isinstance(payload, str) or payload is None:
            parse_failures[str(page_no)] = payload or "missing digitise"
            continue
        slice_ = page_slice(skeleton, page_no)
        allowed_q = {s["q_no"] for s in slice_}
        try:
            questions = parse_digitise_to_questions(payload, slice_)
            p.validate_page_response({"questions": questions}, allowed_q, set())
        except Exception as exc:
            parse_failures[str(page_no)] = f"{type(exc).__name__}: {exc}"
            continue
        by_page[page_no] = questions
        for q in questions:
            parsed[int(q["q_no"])] = {
                "body": q["body"],
                "options": q.get("options"),
                "page": page_no,
            }
    dump(out_dir / "parse_failures.json", parse_failures)
    dump(out_dir / "parsed_raw.json", {str(k): v for k, v in parsed.items()})

    for q_no, spec in specs.items():
        entry = parsed.get(q_no) or {}
        parsed[q_no] = clean_entry(entry, spec)

    cov = coverage_diff(set(specs), set(parsed))
    holds: list[dict] = []
    for q_no in cov["missing"]:
        holds.append({"q_no": q_no, "reason": "coverage_miss", "page": specs[q_no]["page"]})

    gemma_path = out_dir / "gemma4.json"
    flash_path = out_dir / "glm53_flash.json"
    gemma_by_page = json.loads(gemma_path.read_text(encoding="utf-8")) if gemma_path.exists() else {}
    flash_by_page = json.loads(flash_path.read_text(encoding="utf-8")) if flash_path.exists() else {}
    disagreements = []
    vision_ok_q: set[int] = set()
    for page_no, questions in by_page.items():
        slice_ = page_slice(skeleton, page_no)
        spec_by_q = {s["q_no"]: s for s in slice_}
        parse_obs = observer_shape(questions, spec_by_q)
        print(f"vision page {page_no} ({len(questions)} q)", flush=True)
        cached = gemma_by_page.get(str(page_no))
        if question_rows(cached):
            gemma = cached
            print("  gemma4 cached", flush=True)
        else:
            try:
                gemma = observe_page(page_no, slice_, env, limiter)
            except Exception as exc:
                gemma = {"error": f"{type(exc).__name__}: {exc}", "questions": []}
            gemma_by_page[str(page_no)] = gemma
            dump(gemma_path, gemma_by_page)
        if vision_agree(parse_obs, gemma):
            vision_ok_q.update(int(q["q_no"]) for q in questions)
            continue
        disagreements.append({"page": page_no, "parse": parse_obs, "gemma": gemma})
        cached_flash = flash_by_page.get(str(page_no))
        if question_rows(cached_flash):
            flash = cached_flash
            print("  flash cached", flush=True)
        else:
            try:
                flash = tiebreak_page(page_no, slice_, env, limiter)
            except Exception as extra:
                flash = {"error": f"{type(extra).__name__}: {extra}", "questions": []}
            flash_by_page[str(page_no)] = flash
            dump(flash_path, flash_by_page)
        if vision_agree(parse_obs, flash):
            vision_ok_q.update(int(q["q_no"]) for q in questions)
            continue
        if vision_agree(gemma, flash):
            gemma_idx = {int(q["q_no"]): q for q in question_rows(gemma)}
            for q in questions:
                q_no = int(q["q_no"])
                adopted = adopt_from_observer(parsed[q_no], gemma_idx.get(q_no) or {}, specs[q_no])
                adopted = clean_entry(adopted, specs[q_no])
                if shape_ok_for(specs[q_no], adopted) and not is_solver_dump(adopted.get("body") or ""):
                    parsed[q_no] = adopted
                    vision_ok_q.add(q_no)
                else:
                    holds.append({
                        "q_no": q_no,
                        "reason": "vision_conflict",
                        "page": page_no,
                        "detail": "flash agreed with gemma4 but shape failed",
                    })
            continue
        for q in questions:
            holds.append({"q_no": int(q["q_no"]), "reason": "vision_conflict", "page": page_no})

    dump(gemma_path, gemma_by_page)
    dump(flash_path, flash_by_page)
    dump(out_dir / "disagreements.json", disagreements)
    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})

    sb = p.supabase_client()
    q_ids = seed_rows(sb, skeleton)
    print(f"seeded {len(q_ids)} skeleton rows q_no {Q_NO_OFFSET + 1}–{Q_NO_OFFSET + 14}", flush=True)

    solvers = {}
    katex_log = {}
    fig_urls: dict = {}
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no)
        db_id = q_ids.get(q_no)
        if entry is None or db_id is None:
            continue
        print(f"gates q {q_no}/14", flush=True)
        coverage_ok = q_no not in cov["missing"]
        vision_ok = q_no in vision_ok_q
        shape_ok = shape_ok_for(spec, entry)
        audit_ok = row_audit_ok(entry) and not flags_for(entry.get("body") or "", is_option=False)
        if entry.get("options"):
            audit_ok = audit_ok and all(
                not flags_for(o or "", is_option=True) for o in entry["options"]
            )
        try:
            katex_ok = row_katex_ok(entry, env, limiter)
        except Exception as exc:
            katex_ok = False
            katex_log[str(q_no)] = f"{type(exc).__name__}: {exc}"
        else:
            katex_log[str(q_no)] = katex_ok
        if not katex_ok:
            holds.append({"q_no": q_no, "reason": "katex_render"})
        if not shape_ok:
            holds.append({"q_no": q_no, "reason": "shape"})

        key_row = {"type": spec["answer_type"], "value": spec["answer_value"]}
        glm_ans = ds_ans = None
        match = False
        try:
            glm_ans = solver_answer(PRIMARY_SOLVER, entry, spec, fig_urls, env, limiter)
        except Exception as exc:
            glm_err = exc
        else:
            glm_err = None
        if solver_has_answer(str(glm_ans or ""), key_row["type"]):
            match = solve_match(str(glm_ans), "", key_row["type"], key_row["value"])
        else:
            ds_err = None
            for fallback in FALLBACK_SOLVERS:
                try:
                    ds_ans = solver_answer(fallback, entry, spec, fig_urls, env, limiter)
                    break
                except Exception as exc:
                    ds_err = exc
                    ds_ans = None
            if solver_has_answer(str(ds_ans or ""), key_row["type"]):
                match = solve_match("", str(ds_ans), key_row["type"], key_row["value"])
            else:
                detail = glm_err or ds_err
                holds.append({
                    "q_no": q_no,
                    "reason": "empty_model" if detail and "empty" in str(detail) else "solver_parse",
                    "detail": str(detail) if detail else "no solver answer",
                })
        if not match and (glm_ans is not None or ds_ans is not None):
            holds.append({
                "q_no": q_no,
                "reason": "solver_mismatch",
                "pdf_key": key_row["value"],
                "glm": glm_ans,
                "deepseek": ds_ans,
                "stem_preview": (entry.get("body") or "")[:160],
            })
        solvers[str(q_no)] = {
            "glm": glm_ans,
            "deepseek": ds_ans,
            "key": key_row["value"],
            "match": match,
        }
        confidence = 1.0 if vision_ok else 0.5
        gates = {
            "skeleton": True,
            "shape_ok": shape_ok,
            "coverage_ok": coverage_ok,
            "vision_ok": vision_ok,
            "figures_ok": True,
            "audit_ok": audit_ok,
            "katex_ok": katex_ok,
            "solve_match": match,
            "confidence": confidence,
        }
        status = final_publish_status(gates, entry.get("body") or "")
        upsert_question(
            sb, db_id, entry, status,
            confidence if status == "auto_ok" else (1.0 if status == "human_ok" else 0.5),
            spec,
            answer=str(key_row["value"]) if status in ("auto_ok", "human_ok") else None,
        )

    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})
    dump(out_dir / "solvers.json", solvers)
    dump(out_dir / "katex.json", katex_log)
    dump(out_dir / "hold.json", {"chapter_no": 19, "holds": holds})

    statuses = (
        sb.table("pyq_questions")
        .select("q_no,review_status,format")
        .eq("chapter_id", CHAPTER_ID)
        .gte("q_no", Q_NO_OFFSET + 1)
        .lte("q_no", Q_NO_OFFSET + 14)
        .order("q_no")
        .execute()
        .data
    )
    dump(out_dir / "db_status.json", statuses)
    live = [r for r in statuses if r["review_status"] in ("auto_ok", "human_ok")]
    print(f"live {len(live)}/14  holds {len(holds)}", flush=True)
    for h in holds:
        print(f"  hold Q{h.get('q_no')} {h.get('reason')} {h.get('detail') or ''}", flush=True)
    return 2 if any(r["review_status"] not in ("auto_ok", "human_ok") for r in statuses) else 0


if __name__ == "__main__":
    sys.exit(main())
