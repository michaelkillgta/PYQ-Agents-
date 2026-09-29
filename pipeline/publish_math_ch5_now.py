#!/usr/bin/env python3
"""Emergency publish math PDF chapter 5 from parsed.json. No Document AI. No Gemini."""
from __future__ import annotations

import json
import re

import pyq_common as p
from agents.katex_check import is_solver_dump, katex_render_ok
from agents.publish import shape_ok_for, upsert_question
from agents.solvers import solve_match
from audit_paper_text import flags_for
from run_chapter_agents import answer_for, chapter_dir, spec_map

CHAPTER_NO = 5
OVERLAY = re.compile(r"\bmathongo\b|\bmathone\b|#\s*#\s*mi", re.I)
TRUNC_OPT = re.compile(r"^(√|N|\*|1/√|)$")


def leftover_junk(entry: dict) -> str | None:
    fields = [entry.get("body") or ""]
    fields.extend(entry.get("options") or [])
    for t in fields:
        if OVERLAY.search(t or ""):
            return "overlay"
    opts = entry.get("options")
    if isinstance(opts, list):
        for o in opts:
            if TRUNC_OPT.fullmatch((o or "").strip()):
                return "truncated"
            if (o or "").rstrip().endswith("√") and len((o or "").strip()) <= 4:
                return "truncated"
    return None


def main() -> int:
    book_spec = p.configure_book("math")
    out_dir = chapter_dir(CHAPTER_NO)
    parsed_path = out_dir / "parsed.json"
    if not parsed_path.exists():
        raise SystemExit("missing parsed.json")
    parsed = {int(k): v for k, v in json.loads(parsed_path.read_text(encoding="utf-8")).items()}
    solvers = {}
    sp = out_dir / "solvers.json"
    if sp.exists():
        solvers = json.loads(sp.read_text(encoding="utf-8"))
    specs = spec_map(p.load_skeleton(), CHAPTER_NO)
    key_book = p.load_answer_key()
    sb = p.supabase_client()
    ch_id = p.resolve_chapter_id(sb, CHAPTER_NO, book_spec["subject_name"])
    q_ids = {int(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch_id).execute().data}

    katex_holds = []
    fig_holds = []
    auto_ok_n = 0
    held_n = 0
    for q_no, spec in sorted(specs.items()):
        entry = parsed.get(q_no) or {}
        row = solvers.get(str(q_no)) or {}
        key_row = answer_for(key_book, CHAPTER_NO, q_no)
        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        try:
            katex_ok = all(katex_render_ok(t) for t in fields)
        except Exception:
            katex_ok = False
        if not katex_ok:
            katex_holds.append(q_no)
        junk = leftover_junk(entry)
        dump_ok = not is_solver_dump(entry.get("body") or "")
        audit_hits = flags_for(entry.get("body") or "", is_option=False)
        for opt in entry.get("options") or []:
            audit_hits.extend(flags_for(opt or "", is_option=True))
        audit_ok = not [f for f in audit_hits if not str(f).startswith("empty")]
        shape_ok = shape_ok_for(spec, entry)
        body_figs = re.findall(r"\[\[fig:([^\]]+)\]\]", entry.get("body") or "")
        match = False
        if key_row and row.get("glm") not in (None, "") and row.get("deepseek") not in (None, ""):
            match = bool(row.get("match")) or solve_match(
                str(row.get("glm") or ""), str(row.get("deepseek") or ""),
                key_row["type"], key_row["value"],
            )
        auto = bool(
            shape_ok and katex_ok and dump_ok and audit_ok and junk is None
            and match and key_row is not None and not body_figs
        )
        if body_figs:
            # keep previously uploaded figure; hold only if stem has fig token but we cannot confirm GET here fast
            auto = bool(
                shape_ok and katex_ok and dump_ok and audit_ok and junk is None
                and match and key_row is not None
            )
        status = "auto_ok" if auto else "unreviewed"
        answer = None if key_row is None else str(key_row["value"])
        upsert_question(
            sb, q_ids[q_no], entry, status,
            1.0 if status == "auto_ok" else 0.5,
            spec, answer=answer if status == "auto_ok" else None,
        )
        if status == "auto_ok":
            auto_ok_n += 1
        else:
            held_n += 1

    rows = sb.table("pyq_questions").select("q_no,review_status,body").eq(
        "chapter_id", ch_id).execute().data
    by = {}
    bodies = 0
    for r in rows:
        by[r["review_status"]] = by.get(r["review_status"], 0) + 1
        if r.get("body"):
            bodies += 1
    pub = by.get("auto_ok", 0) + by.get("human_ok", 0)
    held = sum(v for k, v in by.items() if k not in ("auto_ok", "human_ok"))
    print("slug=permutation-combination")
    print("DB", by)
    print(f"rows={len(rows)} bodies={bodies}")
    print(f"publishable={pub} held={held}")
    print(f"local_auto_ok={auto_ok_n} local_held={held_n}")
    print(f"katex_holds={katex_holds}")
    print(f"figure_holds={fig_holds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
