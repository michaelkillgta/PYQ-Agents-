#!/usr/bin/env python3
"""Emergency publish Mathematics PDF chapter 4 from parsed.json. No Document AI. No Gemini."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from agents.figures_check import (
    chapter_figure_keys,
    http_get_status,
    missing_figure_gets,
    upload_chapter_figures,
)
from agents.katex_check import (
    _MATH_INNER,
    dollar_runs_ok,
    is_solver_dump,
    leftover_latex_outside_math,
)
from agents.publish import shape_ok_for, upsert_question
from agents.report import build_report
from audit_paper_text import flags_for
from run_chapter_agents import chapter_dir, dump, spec_map, write_hold_json

CHAPTER_NO = 4
BOOK = "math"
TRUNC_OPT = re.compile(r"^(√|N|\*|1/√|)$")
KATEX_BATCH = Path(__file__).resolve().parent / "batch_katex_probe.mjs"


def extract_figure_png(key: str) -> Path:
    dest = p.OUT / "figures" / f"{key}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    m = re.fullmatch(r"p(\d{3})_x(\d+)", key)
    if not m:
        raise ValueError(f"bad figure key {key}")
    xref = int(m.group(2))
    doc = pymupdf.open(p.PDF_PATH)
    pix = pymupdf.Pixmap(doc, xref)
    if pix.n - pix.alpha > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    pix.save(str(dest))
    doc.close()
    return dest


def attach_fig_tokens(entry: dict, spec: dict) -> dict:
    out = dict(entry)
    body = out.get("body") or ""
    for key in spec.get("figure_keys") or []:
        token = f"[[fig:{key}]]"
        if token not in body:
            body = (body.rstrip() + "\n\n" + token).strip()
    out["body"] = body
    return out


def leftover_junk(entry: dict) -> str | None:
    fields = [entry.get("body") or ""]
    fields.extend(entry.get("options") or [])
    opts = entry.get("options")
    if isinstance(opts, list):
        for o in opts:
            t = (o or "").strip()
            if TRUNC_OPT.fullmatch(t):
                return "truncated"
            if t.endswith("√") and len(t) <= 4:
                return "truncated"
    body = (entry.get("body") or "").strip()
    if not body or body.startswith("(OCR missed"):
        return "truncated"
    if body.endswith((" thi", " th", " the")):
        return "truncated"
    return None


def row_audit_ok(entry: dict) -> bool:
    hits = flags_for(entry.get("body") or "", is_option=False)
    for opt in entry.get("options") or []:
        hits.extend(flags_for(opt or "", is_option=True))
    blocking = [f for f in hits if not str(f).startswith("empty")]
    return not blocking


def collect_tex(texts: list[str]) -> tuple[list[list[int] | None], list[str]]:
    index: list[list[int] | None] = []
    snippets: list[str] = []
    for t in texts:
        if not dollar_runs_ok(t) or leftover_latex_outside_math(t):
            index.append(None)
            continue
        ids: list[int] = []
        for m in _MATH_INNER.finditer(t or ""):
            ids.append(len(snippets))
            snippets.append(m.group(1))
        index.append(ids)
    return index, snippets


def probe_all(snippets: list[str]) -> list[bool]:
    if not snippets:
        return []
    if not KATEX_BATCH.exists():
        KATEX_BATCH.write_text(
            'import { createRequire } from "module";\n'
            'import fs from "fs";\n'
            'const require = createRequire(import.meta.url);\n'
            'const katex = require("C:/Users/tempo/Downloads/EduBlast/Web/node_modules/katex");\n'
            'const items = JSON.parse(fs.readFileSync(0, "utf8"));\n'
            'const out = [];\n'
            'for (const tex of items) {\n'
            '  try {\n'
            '    katex.renderToString(tex, { throwOnError: true, displayMode: false });\n'
            '    out.push(true);\n'
            '  } catch {\n'
            '    out.push(false);\n'
            '  }\n'
            '}\n'
            'process.stdout.write(JSON.stringify(out));\n',
            encoding="utf-8",
        )
    raw = json.dumps(snippets, ensure_ascii=False)
    r = subprocess.run(
        ["node", str(KATEX_BATCH)],
        input=raw,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout or "katex batch failed")
    ok = json.loads(r.stdout)
    if len(ok) != len(snippets):
        raise RuntimeError("katex batch length mismatch")
    return [bool(x) for x in ok]


def fields_katex_ok(fields: list[str], probe: list[bool], index: list[list[int] | None], start: int) -> bool:
    for offset, field in enumerate(fields):
        ids = index[start + offset]
        if ids is None:
            return False
        if any(not probe[i] for i in ids):
            return False
        del field
    return True


def main() -> int:
    book_spec = p.configure_book(BOOK)
    skeleton_all = p.load_skeleton()
    specs = spec_map(skeleton_all, CHAPTER_NO)
    out_dir = chapter_dir(CHAPTER_NO)
    pages = sorted({r["page"] for r in specs.values()})
    print(f"math chapter {CHAPTER_NO}: {len(specs)} questions, pages {pages[0]}-{pages[-1]}", flush=True)

    ocr_dir = p.OUT / "ocr"
    missing_ocr = [n for n in pages if not (ocr_dir / f"page_{n:03d}.json").exists()]
    if missing_ocr:
        raise SystemExit(f"OCR cache miss; refusing Document AI: {missing_ocr}")

    parsed_path = out_dir / "parsed.json"
    if not parsed_path.exists():
        raise SystemExit(f"missing {parsed_path}")
    raw_parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
    parsed = {int(k): attach_fig_tokens(v, specs[int(k)]) for k, v in raw_parsed.items() if int(k) in specs}

    wanted_keys = chapter_figure_keys(skeleton_all, CHAPTER_NO)
    for key in wanted_keys:
        extract_figure_png(key)

    sb = p.supabase_client()
    fig_urls = upload_chapter_figures(CHAPTER_NO, sb)
    key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
    missing_figs = missing_figure_gets(key_to_url, http_get_status)
    if missing_figs:
        fig_urls = upload_chapter_figures(CHAPTER_NO, sb)
        key_to_url = {k: fig_urls.get(k, "") for k in wanted_keys}
        missing_figs = missing_figure_gets(key_to_url, http_get_status)
    ok_fig_keys = {k for k in wanted_keys if k not in missing_figs}
    holds = [{"q_no": None, "reason": "figure_get", "figure_key": k, "decision": None}
             for k in missing_figs]
    print(f"figures wanted={wanted_keys} missing={missing_figs}", flush=True)

    ch_id = p.resolve_chapter_id(sb, CHAPTER_NO, book_spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    ordered = sorted(specs.items())
    flat_fields: list[str] = []
    field_starts: dict[int, tuple[int, int]] = {}
    for q_no, spec in ordered:
        entry = parsed.get(q_no)
        if entry is None:
            continue
        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        field_starts[q_no] = (len(flat_fields), len(fields))
        flat_fields.extend(fields)
    index, snippets = collect_tex(flat_fields)
    print(f"katex snippets {len(snippets)} across {len(flat_fields)} fields", flush=True)
    probe = probe_all(snippets)

    katex_log = {}
    publishable = []
    held_q = set()
    for q_no, spec in ordered:
        entry = parsed.get(q_no)
        if entry is None:
            holds.append({"q_no": q_no, "reason": "coverage_miss", "page": spec["page"], "decision": None})
            held_q.add(q_no)
            continue
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", entry.get("body") or "")
        figures_ok = all(k in ok_fig_keys for k in body_figs) and all(
            k in ok_fig_keys for k in (spec.get("figure_keys") or [])
        )
        shape_ok = shape_ok_for(spec, entry)
        junk = leftover_junk(entry)
        dump_ok = not is_solver_dump(entry.get("body") or "")
        audit_ok = row_audit_ok(entry) and junk is None
        start, nfields = field_starts[q_no]
        fields = flat_fields[start:start + nfields]
        katex_ok = fields_katex_ok(fields, probe, index, start)
        katex_log[str(q_no)] = katex_ok
        pdf_key = spec.get("answer_value")
        if pdf_key is None or str(pdf_key).strip() == "":
            holds.append({"q_no": q_no, "reason": "solver_parse", "detail": "no PDF key", "decision": None})
        if not katex_ok:
            holds.append({"q_no": q_no, "reason": "katex_render", "decision": None})
        if not shape_ok:
            holds.append({"q_no": q_no, "reason": "shape", "decision": None})
        if junk:
            holds.append({"q_no": q_no, "reason": junk, "decision": None})
        if not dump_ok:
            holds.append({"q_no": q_no, "reason": "solver_prose", "decision": None})
        if not figures_ok:
            holds.append({"q_no": q_no, "reason": "figure_get", "decision": None})
        if not audit_ok and junk is None:
            holds.append({"q_no": q_no, "reason": "shape", "detail": "audit", "decision": None})

        ok = (
            katex_ok and shape_ok and dump_ok and audit_ok and figures_ok
            and pdf_key is not None and str(pdf_key).strip() != ""
        )
        qid = q_ids.get(q_no)
        if qid is None:
            holds.append({"q_no": q_no, "reason": "coverage_miss", "detail": "no db row", "decision": None})
            held_q.add(q_no)
            continue
        if ok:
            upsert_question(sb, qid, entry, "human_ok", 1.0, spec, answer=str(pdf_key))
            publishable.append(q_no)
        else:
            upsert_question(sb, qid, entry, "unreviewed", 0.5, spec)
            held_q.add(q_no)
        if q_no % 40 == 0 or q_no == 1:
            print(f"published through q {q_no}", flush=True)

    dump(out_dir / "parsed.json", {str(k): v for k, v in parsed.items()})
    dump(out_dir / "katex.json", katex_log)
    write_hold_json(out_dir, CHAPTER_NO, holds)
    report = build_report(CHAPTER_NO, holds)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report, flush=True)

    db_rows = sb.table("pyq_questions").select("q_no,review_status").eq(
        "chapter_id", ch_id).execute().data
    from collections import Counter
    status_counts = Counter(r["review_status"] for r in db_rows)
    katex_holds = sorted({h["q_no"] for h in holds if h.get("reason") == "katex_render" and h.get("q_no")})
    fig_holds = [h.get("figure_key") or h.get("q_no") for h in holds if h.get("reason") == "figure_get"]
    print("SLUG sequences-and-series", flush=True)
    print(f"PUBLISHABLE {len(publishable)} HELD {len(held_q)} TOTAL {len(specs)}", flush=True)
    print(f"DB {dict(status_counts)}", flush=True)
    print(f"KATEX_HOLDS {len(katex_holds)} {katex_holds}", flush=True)
    print(f"FIGURE_HOLDS {fig_holds}", flush=True)
    return 2 if held_q or missing_figs else 0


if __name__ == "__main__":
    sys.exit(main())
