#!/usr/bin/env python3
"""Fix smashed TeX on the ten screenshot chapters; inventory figures + held."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

import pyq_common as p
from agents.katex_check import smashed_tex

SUBJECT = "Mathematics"
SLUGS = [
    "basic-of-mathematics",
    "complex-number",
    "binomial-theorem",
    "determinants",
    "continuity-and-differentiability",
    "application-of-derivatives",
    "definite-integration",
    "area-under-curves",
    "differential-equations",
    "circle",
]
SELECT = (
    "id,q_no,review_status,exam_date,source_bbox,format,body,solution_md,tips_md,formulas_md,"
    "correct_option,numerical_answer,"
    "question_options:pyq_question_options(id,option_index,body)"
)
TAB_EXT = re.compile(r"\text\{")  # after we convert tab to \t this is \t + ext{
# Real pattern: TAB character + "ext{"
TAB_TEXT = re.compile("\t" + r"ext\{")
DBL_CMD = re.compile(r"\\\\(lim|int|sum|prod|frac|sqrt|left|right|infty|to|cdot|times|pi|theta|alpha|beta)\b")
ASCII_SQRT = re.compile(r"\bsqrt\d|\bSQRT|1/sqrt", re.I)
FIG_RE = re.compile(r"\[\[fig:([a-zA-Z0-9_]+)\]\]")


def math_chapters(sb):
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
    units = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    return (
        sb.table("pyq_chapters")
        .select("id,chapter_no,catalog_slug,name")
        .in_("unit_id", units)
        .in_("catalog_slug", SLUGS)
        .execute()
        .data
        or []
    )


def fetch_all(sb, chapter_id: str) -> list[dict]:
    out = []
    start = 0
    while True:
        chunk = (
            sb.table("pyq_questions")
            .select(SELECT)
            .eq("chapter_id", chapter_id)
            .range(start, start + 999)
            .execute()
            .data
            or []
        )
        out.extend(chunk)
        if len(chunk) < 1000:
            break
        start += 1000
    return out


def repair_tex(s: str) -> str:
    if not s:
        return s
    out = TAB_TEXT.sub(r"\\text{", s)
    out = DBL_CMD.sub(r"\\\1", out)
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    dry = "--dry" in sys.argv
    chapters = math_chapters(sb)
    qids = []
    held = []
    nat_empty = []
    mcq_empty = []
    ascii_hits = []
    fig_from_text = []
    patched_q = 0
    patched_opt = 0
    for ch in sorted(chapters, key=lambda r: int(r["chapter_no"])):
        rows = fetch_all(sb, ch["id"])
        print(f"ch{ch['chapter_no']} {ch['catalog_slug']} n={len(rows)}", flush=True)
        for row in rows:
            qids.append(row["id"])
            live = row.get("review_status") in {"auto_ok", "human_ok"}
            if not live:
                held.append(
                    {
                        "ch": ch["chapter_no"],
                        "q": row["q_no"],
                        "id": row["id"],
                        "booklet": (row.get("source_bbox") or {}).get("booklet"),
                        "status": row.get("review_status"),
                    }
                )
                continue
            body2 = repair_tex(row.get("body") or "")
            sol2 = repair_tex(row.get("solution_md") or "")
            tips2 = repair_tex(row.get("tips_md") or "")
            form2 = repair_tex(row.get("formulas_md") or "")
            q_patch = {}
            if body2 != (row.get("body") or ""):
                q_patch["body"] = body2
            if sol2 != (row.get("solution_md") or ""):
                q_patch["solution_md"] = sol2
            if tips2 != (row.get("tips_md") or ""):
                q_patch["tips_md"] = tips2
            if form2 != (row.get("formulas_md") or ""):
                q_patch["formulas_md"] = form2
            if q_patch:
                print(
                    f"  patch Q{row['q_no']} {row['id'][:8]} fields={list(q_patch)} smashed_after={smashed_tex(body2)}",
                    flush=True,
                )
                if not dry:
                    sb.table("pyq_questions").update(q_patch).eq("id", row["id"]).execute()
                patched_q += 1
            if ASCII_SQRT.search(form2 or "") or ASCII_SQRT.search(tips2 or ""):
                ascii_hits.append({"id": row["id"], "q": row["q_no"], "ch": ch["chapter_no"]})
            for key in FIG_RE.findall((body2 or "") + "\n" + (sol2 or "")):
                fig_from_text.append((row["id"], key))
            fmt = (row.get("format") or "").lower()
            opts = row.get("question_options") or []
            for o in opts:
                raw = o.get("body") or ""
                fixed = repair_tex(raw)
                if fixed != raw:
                    print(f"  patch opt Q{row['q_no']} i={o.get('option_index')}", flush=True)
                    if not dry:
                        sb.table("pyq_question_options").update({"body": fixed}).eq("id", o["id"]).execute()
                    patched_opt += 1
                if not raw.strip() or raw.strip() in {"√", "N", "*"}:
                    rec = {"ch": ch["chapter_no"], "q": row["q_no"], "i": o.get("option_index"), "fmt": fmt, "id": row["id"]}
                    if "num" in fmt or fmt in {"integer", "numerical", "nat"}:
                        nat_empty.append(rec)
                    else:
                        mcq_empty.append(rec)
    print(f"patched questions={patched_q} options={patched_opt} dry={dry}", flush=True)
    print(f"held={len(held)} ascii_sqrt_coach={len(ascii_hits)} mcq_empty_opts={len(mcq_empty)} nat_empty={len(nat_empty)}", flush=True)
    print("held list:", flush=True)
    for h in held:
        print(f"  ch{h['ch']} q{h['q']} {h['booklet']} {h['status']} {h['id']}", flush=True)
    print("mcq empty opts:", flush=True)
    for rec in mcq_empty[:40]:
        print(" ", rec, flush=True)

    # figure links for these questions
    links = []
    for i in range(0, len(qids), 80):
        chunk = (
            sb.table("pyq_figure_links")
            .select("question_id,role,figures:pyq_figures(figure_key,storage_path,public_url)")
            .in_("question_id", qids[i : i + 80])
            .execute()
            .data
            or []
        )
        links.extend(chunk)
    print(f"figure_links={len(links)} text_fig_mentions={len(fig_from_text)}", flush=True)
    urls = []
    linked_keys = set()
    for link in links:
        fig = link.get("figures")
        if isinstance(fig, list):
            fig = fig[0] if fig else {}
        if not isinstance(fig, dict):
            continue
        key = fig.get("figure_key")
        if key:
            linked_keys.add(key)
        url = (fig.get("public_url") or "").strip()
        if not url:
            base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
            path = str(fig.get("storage_path") or "").lstrip("/")
            if not path.startswith("pyq/"):
                path = f"pyq/{path}"
            url = f"{base}/storage/v1/object/public/{path}"
        if url:
            urls.append((key, url))
    missing_link = [(qid, k) for qid, k in fig_from_text if k not in linked_keys]
    print(f"unique figure urls={len(dict(urls))} text keys missing link={len(missing_link)}", flush=True)
    for rec in missing_link[:30]:
        print("  missing", rec, flush=True)

    bad = []

    def ping(pair):
        key, url = pair
        try:
            r = httpx.get(url, timeout=20.0)
            return key, url, r.status_code, len(r.content)
        except Exception as exc:
            return key, url, 0, str(exc)

    uniq = dict(urls)
    with ThreadPoolExecutor(max_workers=16) as pool:
        for key, url, status, nbytes in pool.map(ping, uniq.items()):
            if status != 200 or (isinstance(nbytes, int) and nbytes < 24):
                bad.append({"key": key, "status": status, "bytes": nbytes, "url": url})
    print(f"bad GET {len(bad)} / {len(uniq)}", flush=True)
    for b in bad[:20]:
        print(" ", b, flush=True)

    dest = Path(r"c:\Users\tempo\Downloads\files\out-math-named\corner_repair.json")
    dest.write_text(
        json.dumps(
            {
                "patched_q": patched_q,
                "patched_opt": patched_opt,
                "held": held,
                "ascii_hits": ascii_hits[:50],
                "ascii_n": len(ascii_hits),
                "mcq_empty": mcq_empty,
                "missing_link": missing_link[:80],
                "fig_urls": len(uniq),
                "bad_get": bad,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print("wrote", dest, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
