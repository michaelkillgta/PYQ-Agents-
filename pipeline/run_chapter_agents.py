#!/usr/bin/env python3
"""Two-observer chapter ingest. glm5.3 is the primary text solver.

    python run_chapter_agents.py --chapter 5
    python run_chapter_agents.py --book math --chapter 1
    python run_chapter_agents.py --chapter 5 --apply-holds out/agents/chapter_5/hold.json

Exit 0 if zero holds. Exit 2 if holds remain. Never quote accuracy.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pyq_common as p
from agents.coverage import coverage_diff
from agents.figures_check import (
    chapter_figure_keys,
    http_get_status,
    missing_figure_gets,
    upload_chapter_figures,
)
from agents.holds import apply_hold_decision
from agents.katex_check import katex_render_ok, needs_llm_wrap
from agents.models import IMAGE_MODELS, PRIMARY_SOLVER, FALLBACK_SOLVERS, TIEBREAK_MODEL, VISION_MODEL
from agents.promotion import final_publish_status
from agents.publish import promote_shape_valid, shape_ok_for, upsert_question
from agents.report import build_report
from agents.solvers import solve_match, solver_has_answer
from agents.vision import observer_shape, question_rows, vision_agree
from audit_paper_text import flags_for
from bakeoff import page_slice
from parse_ocr_page import parse_digitise_to_questions

OBSERVER_SYSTEM = """You look at a printed JEE Main PYQ book page PNG.
Return JSON:
{"questions":[{"q_no":int,"mcq":bool,"option_count":0 or 4,"has_figure":bool,"body_preview":str,"body":str,"options":[str,str,str,str]|null}]}
Use ONLY the supplied q_no values. Transcribe; do not solve.
MCQ: option_count 4 and four printed options, or option_count 0 and options null if they are unreadably images.
Numerical: mcq false, option_count 0, options null.
Where a figure belongs, keep [[fig:KEY]] using only supplied keys."""

SOLVER_SYSTEM = """Solve this JEE Main question.
Reply JSON {"answer":"..."} only.
MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units.
Do not explain."""

WRAP_SYSTEM = """Wrap every math expression in $...$ KaTeX. Return JSON {"text":"..."}.
Do not change meaning. Do not add or drop [[fig:KEY]] tokens."""


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def chapter_dir(chapter_no: int) -> Path:
    return p.OUT / "agents" / f"chapter_{chapter_no}"


def spec_map(skeleton: list, chapter_no: int) -> dict[int, dict]:
    return {int(r["q_no"]): r for r in skeleton if r["chapter_no"] == chapter_no}


def answer_for(key_book: dict, chapter_no: int, q_no: int) -> dict | None:
    ch = key_book.get(str(chapter_no)) or {}
    return (ch.get("answers") or {}).get(str(q_no))


def bust_ocr_cache(page_no: int) -> None:
    """Keep completed OCR JSON. Re-parse from cache; never re-pay Document AI."""
    return


def parse_pages(skeleton: list, chapter_no: int, digitise: dict) -> tuple[dict, dict, dict]:
    parsed, failures, by_page = {}, {}, {}
    pages = sorted({r["page"] for r in skeleton if r["chapter_no"] == chapter_no})
    for page_no in pages:
        payload = digitise.get(page_no)
        if isinstance(payload, str) or payload is None:
            failures[str(page_no)] = payload or "missing digitise"
            continue
        slice_ = page_slice(skeleton, page_no)
        allowed_q = {s["q_no"] for s in slice_}
        allowed_f = {k for s in slice_ for k in s["figure_keys"]}
        try:
            questions = parse_digitise_to_questions(payload, slice_)
            p.validate_page_response({"questions": questions}, allowed_q, allowed_f)
        except Exception as exc:
            failures[str(page_no)] = f"{type(exc).__name__}: {exc}"
            continue
        by_page[page_no] = questions
        for q in questions:
            parsed[int(q["q_no"])] = {
                "body": q["body"],
                "options": q.get("options"),
                "page": page_no,
            }
    return parsed, failures, by_page


def v2_json(model: str, messages: list, env: dict, limiter: p.RateLimiter,
            json_object: bool = True) -> dict:
    max_tokens = 8192 if model in IMAGE_MODELS else 2048
    raw = p.call_sarvam_v2(
        model, messages, env["SARVAM_API_KEY"], limiter,
        max_tokens=max_tokens, json_object=json_object,
    )
    return p.parse_json_content(raw)


def wrap_if_needed(text: str, env: dict, limiter: p.RateLimiter) -> str:
    if not needs_llm_wrap(text):
        return text
    messages = [
        {"role": "system", "content": WRAP_SYSTEM},
        {"role": "user", "content": text},
    ]
    try:
        data = v2_json(PRIMARY_SOLVER, messages, env, limiter)
        return str(data.get("text") or text)
    except Exception:
        return text


def row_audit_ok(entry: dict) -> bool:
    hits = flags_for(entry.get("body") or "", is_option=False)
    for opt in entry.get("options") or []:
        hits.extend(flags_for(opt or "", is_option=True))
    blocking = [f for f in hits if not str(f).startswith("empty")]
    return not blocking


def row_katex_ok(entry: dict, env: dict, limiter: p.RateLimiter) -> bool:
    fields = [entry.get("body") or ""]
    fields.extend(entry.get("options") or [])
    wrapped = [wrap_if_needed(t, env, limiter) for t in fields]
    entry["body"] = wrapped[0]
    if entry.get("options"):
        entry["options"] = wrapped[1:]
    return all(katex_render_ok(t) for t in wrapped)


def solver_answer(model: str, entry: dict, spec: dict, fig_urls: dict,
                  env: dict, limiter: p.RateLimiter) -> str:
    opts = entry.get("options")
    opt_lines = ""
    if isinstance(opts, list):
        opt_lines = "\n".join(f"({i}) {t}" for i, t in enumerate(opts, start=1))
    figs = re.findall(r"\[\[fig:([^\]]+)\]\]", entry.get("body") or "")
    fig_lines = "\n".join(f"{k}: {fig_urls.get(k, '')}" for k in figs)
    user = (
        f"Type: {spec['answer_type']}\n"
        f"Stem:\n{entry.get('body') or ''}\n"
        f"{opt_lines}\n"
        f"{fig_lines}"
    )
    messages = [
        {"role": "system", "content": SOLVER_SYSTEM},
        {"role": "user", "content": user},
    ]
    last_err = None
    for _ in range(2):
        try:
            data = v2_json(model, messages, env, limiter)
            ans = data.get("answer")
            if ans is None or str(ans).strip() == "":
                raise ValueError("empty model content")
            return str(ans).strip()
        except Exception as exc:
            last_err = exc
    raise last_err or ValueError("empty model content")


def observe_page(page_no: int, slice_: list, env: dict,
                 limiter: p.RateLimiter) -> dict:
    png = p.OUT / "pages" / f"page_{page_no:03d}.png"
    allowed = [{"q_no": s["q_no"], "figure_keys": s["figure_keys"],
                "answer_type": s["answer_type"]} for s in slice_]
    text = (
        f"Page {page_no}. Questions on this page:\n"
        + json.dumps(allowed, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": OBSERVER_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    return v2_json(VISION_MODEL, messages, env, limiter)


def tiebreak_page(page_no: int, slice_: list, env: dict,
                  limiter: p.RateLimiter) -> dict:
    png = p.OUT / "pages" / f"page_{page_no:03d}.png"
    allowed = [{"q_no": s["q_no"], "figure_keys": s["figure_keys"],
                "answer_type": s["answer_type"]} for s in slice_]
    text = (
        f"Page {page_no}. Tie-break. Questions on this page:\n"
        + json.dumps(allowed, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": OBSERVER_SYSTEM}]
    messages.extend(p.page_image_message(png, text))
    return v2_json(TIEBREAK_MODEL, messages, env, limiter)


def adopt_from_observer(entry: dict, observer_q: dict, spec: dict) -> dict:
    body = observer_q.get("body")
    options = observer_q.get("options")
    if not body:
        return entry
    next_entry = dict(entry)
    next_entry["body"] = body
    if spec["answer_type"] == "mcq" and isinstance(options, list) and len(options) == 4:
        next_entry["options"] = options
    elif spec["answer_type"] != "mcq":
        next_entry["options"] = None
    return next_entry


def write_hold_json(out_dir: Path, chapter_no: int, holds: list) -> None:
    dump(out_dir / "hold.json", {"chapter_no": chapter_no, "holds": holds})


def apply_holds_path(chapter_no: int, hold_path: Path, book: str) -> int:
    spec = p.configure_book(book)
    env = p.load_env()
    limiter = p.RateLimiter(60)
    payload = json.loads(hold_path.read_text(encoding="utf-8"))
    holds = payload.get("holds") or []
    out_dir = chapter_dir(chapter_no)
    parsed = json.loads((out_dir / "parsed.json").read_text(encoding="utf-8"))
    skeleton = spec_map(p.load_skeleton(), chapter_no)
    sb = p.supabase_client()
    ch_id = p.resolve_chapter_id(sb, chapter_no, spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    remaining = []
    for hold in holds:
        if hold.get("q_no") is None:
            remaining.append(hold)
            continue
        q_no = int(hold["q_no"])
        spec = skeleton[q_no]
        entry = parsed.get(str(q_no)) or parsed.get(q_no) or {}
        mapped = apply_hold_decision(hold)
        if mapped["review_status"] != "human_ok":
            remaining.append({**hold, "decision": hold.get("decision") or "leave_unreviewed"})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        if not row_katex_ok(entry, env, limiter):
            remaining.append({**hold, "reason": "katex_render",
                              "detail": "still failing after apply-holds"})
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            continue
        upsert_question(
            sb, q_ids[q_no], entry, "human_ok", 1.0, spec,
            answer=mapped["answer"],
        )

    write_hold_json(out_dir, chapter_no, remaining)
    report = build_report(chapter_no, remaining)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    return 2 if remaining else 0


def run_chapter(chapter_no: int, book: str) -> int:
    book_spec = p.configure_book(book)
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = p.load_skeleton()
    specs = spec_map(skeleton, chapter_no)
    if not specs:
        raise SystemExit(f"no skeleton rows for chapter {chapter_no}")
    out_dir = chapter_dir(chapter_no)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted({r["page"] for r in specs.values()})
    print(f"{book} chapter {chapter_no}: {len(specs)} questions, pages {pages}")

    digitise = p.digitise_pages_parallel(pages, env["SARVAM_API_KEY"], workers=4)
    dump(out_dir / "digitise_failures.json",
         {str(k): v for k, v in digitise.items() if isinstance(v, str)})

    parsed, parse_failures, by_page = parse_pages(skeleton, chapter_no, digitise)
    dump(out_dir / "parse_failures.json", parse_failures)

    skeleton_q = set(specs)
    parsed_q = set(parsed)
    cov = coverage_diff(skeleton_q, parsed_q)
    if cov["extra"]:
        raise SystemExit(f"extra q_no not in skeleton: {cov['extra']}")

    retried_pages = set()
    for q_no in cov["missing"]:
        page_no = specs[q_no]["page"]
        if page_no in retried_pages:
            continue
        retried_pages.add(page_no)
        bust_ocr_cache(page_no)
        try:
            digitise[page_no] = p.digitise_page(page_no, env["SARVAM_API_KEY"])
        except Exception as exc:
            digitise[page_no] = f"{type(exc).__name__}: {exc}"
    if retried_pages:
        parsed, parse_failures, by_page = parse_pages(skeleton, chapter_no, digitise)
        dump(out_dir / "parse_failures.json", parse_failures)
        cov = coverage_diff(set(specs), set(parsed))

    holds = []
    for q_no in cov["missing"]:
        holds.append({
            "q_no": q_no,
            "reason": "coverage_miss",
            "page": specs[q_no]["page"],
            "decision": None,
        })

    parsed_out = {str(k): v for k, v in parsed.items()}
    dump(out_dir / "parsed.json", parsed_out)

    sb = p.supabase_client()
    fig_urls = upload_chapter_figures(chapter_no, sb)
    wanted_keys = chapter_figure_keys(skeleton, chapter_no)
    key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
    missing_figs = missing_figure_gets(key_to_url, http_get_status)
    if missing_figs:
        fig_urls = upload_chapter_figures(chapter_no, sb)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
    ok_fig_keys = {k for k in wanted_keys if k not in missing_figs}
    for key in missing_figs:
        holds.append({
            "q_no": None,
            "reason": "figure_get",
            "figure_key": key,
            "decision": None,
        })

    gemma_path = out_dir / "gemma4.json"
    flash_path = out_dir / "glm53_flash.json"
    gemma_by_page = json.loads(gemma_path.read_text(encoding="utf-8")) if gemma_path.exists() else {}
    flash_by_page = json.loads(flash_path.read_text(encoding="utf-8")) if flash_path.exists() else {}
    disagreements = []
    vision_ok_q = set()
    for page_no, questions in by_page.items():
        slice_ = page_slice(skeleton, page_no)
        spec_by_q = {s["q_no"]: s for s in slice_}
        parse_obs = observer_shape(questions, spec_by_q)
        print(f"vision page {page_no} ({len(questions)} q)", flush=True)
        cached = gemma_by_page.get(str(page_no))
        if question_rows(cached):
            gemma = cached
            print(f"  gemma4 cached", flush=True)
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
            print(f"  flash cached", flush=True)
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
                if shape_ok_for(specs[q_no], adopted):
                    parsed[q_no] = adopted
                    vision_ok_q.add(q_no)
                else:
                    holds.append({
                        "q_no": q_no,
                        "reason": "vision_conflict",
                        "page": page_no,
                        "detail": "flash agreed with gemma4 but shape failed",
                        "decision": None,
                    })
            continue
        for q in questions:
            holds.append({
                "q_no": int(q["q_no"]),
                "reason": "vision_conflict",
                "page": page_no,
                "decision": None,
            })

    dump(gemma_path, gemma_by_page)
    dump(flash_path, flash_by_page)
    dump(out_dir / "disagreements.json", disagreements)
    parsed_out = {str(k): v for k, v in parsed.items()}
    dump(out_dir / "parsed.json", parsed_out)

    key_book = p.load_answer_key()
    solvers = {}
    ch_id = p.resolve_chapter_id(sb, chapter_no, book_spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    katex_log = {}
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no)
        if entry is None:
            continue
        if q_no % 10 == 0 or q_no == 1:
            print(f"gates q {q_no}/{len(specs)}", flush=True)
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", entry.get("body") or "")
        figures_ok = all(k in ok_fig_keys for k in body_figs) and not any(
            h.get("figure_key") in body_figs for h in holds if h.get("reason") == "figure_get"
        )
        coverage_ok = q_no not in cov["missing"]
        vision_ok = q_no in vision_ok_q
        shape_ok = shape_ok_for(spec, entry)
        audit_ok = row_audit_ok(entry)
        try:
            katex_ok = row_katex_ok(entry, env, limiter)
        except Exception as exc:
            katex_ok = False
            katex_log[str(q_no)] = f"{type(exc).__name__}: {exc}"
        else:
            katex_log[str(q_no)] = katex_ok
        if not katex_ok:
            holds.append({
                "q_no": q_no,
                "reason": "katex_render",
                "decision": None,
            })
        if not shape_ok:
            holds.append({
                "q_no": q_no,
                "reason": "shape",
                "decision": None,
            })

        key_row = answer_for(key_book, chapter_no, q_no)
        glm_ans = ds_ans = None
        match = False
        if key_row is None:
            holds.append({
                "q_no": q_no,
                "reason": "solver_parse",
                "detail": "no answer_key row",
                "decision": None,
            })
        else:
            try:
                glm_ans = solver_answer(PRIMARY_SOLVER, entry, spec, fig_urls, env, limiter)
            except Exception as exc:
                glm_ans = None
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
                        "decision": None,
                    })
            if not match and (glm_ans is not None or ds_ans is not None):
                holds.append({
                    "q_no": q_no,
                    "reason": "solver_mismatch",
                    "pdf_key": key_row["value"],
                    "glm": glm_ans,
                    "deepseek": ds_ans,
                    "stem_preview": (entry.get("body") or "")[:160],
                    "decision": None,
                })

        solvers[str(q_no)] = {
            "glm": glm_ans,
            "deepseek": ds_ans,
            "key": None if key_row is None else key_row["value"],
            "match": match,
        }

        confidence = 1.0 if vision_ok else 0.5
        gates = {
            "skeleton": True,
            "shape_ok": shape_ok,
            "coverage_ok": coverage_ok,
            "vision_ok": vision_ok,
            "figures_ok": figures_ok,
            "audit_ok": audit_ok,
            "katex_ok": katex_ok,
            "solve_match": match,
            "confidence": confidence,
        }
        status = final_publish_status(gates, entry.get("body") or "")
        answer = None if key_row is None else str(key_row["value"])
        upsert_question(
            sb, q_ids[q_no], entry, status,
            confidence if status == "auto_ok" else (1.0 if status == "human_ok" else 0.5),
            spec, answer=answer if status in ("auto_ok", "human_ok") else None,
        )

    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})
    dump(out_dir / "solvers.json", solvers)
    dump(out_dir / "katex.json", katex_log)
    write_hold_json(out_dir, chapter_no, holds)
    report = build_report(chapter_no, holds)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    return 2 if holds else 0


def promote_chapter(chapter_no: int, book: str) -> int:
    book_spec = p.configure_book(book)
    skeleton = spec_map(p.load_skeleton(), chapter_no)
    if not skeleton:
        raise SystemExit(f"no skeleton rows for chapter {chapter_no}")
    out_dir = chapter_dir(chapter_no)
    parsed_path = out_dir / "parsed.json"
    if not parsed_path.exists():
        raise SystemExit(f"missing {parsed_path}")
    parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
    sb = p.supabase_client()
    ch_id = p.resolve_chapter_id(sb, chapter_no, book_spec["subject_name"])
    q_rows = sb.table("pyq_questions").select("id,q_no,review_status").eq(
        "chapter_id", ch_id).execute().data
    q_ids = {int(r["q_no"]): r["id"] for r in q_rows}
    existing = {int(r["q_no"]): r["review_status"] for r in q_rows}
    promoted, held = promote_shape_valid(sb, q_ids, skeleton, parsed, existing)
    print(f"promoted human_ok={promoted} still unreviewed={held} kept auto_ok="
          f"{sum(1 for s in existing.values() if s == 'auto_ok')}")
    return 0 if held == 0 else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--book", choices=sorted(p.BOOKS), default="physics")
    ap.add_argument("--apply-holds", dest="apply_holds")
    ap.add_argument("--promote-shape", action="store_true")
    args = ap.parse_args(argv)
    p.configure_book(args.book)
    if args.apply_holds:
        return apply_holds_path(args.chapter, Path(args.apply_holds), args.book)
    if args.promote_shape:
        return promote_chapter(args.chapter, args.book)
    return run_chapter(args.chapter, args.book)


if __name__ == "__main__":
    sys.exit(main())
