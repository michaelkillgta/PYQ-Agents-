#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pyq_common as p
from agents.katex_check import smashed_tex

NESTED_FRAC = re.compile(r"\\frac\s*\{\s*\\frac")
FIG_RE = re.compile(r"\[\[fig:([a-zA-Z0-9_]+)\]\]")

rep = json.loads(Path(r"c:\Users\tempo\Downloads\files\out-math-named\corner_audit.json").read_text(encoding="utf-8"))

print("=== chapters ===")
for c in rep["chapters"]:
    print(
        f"ch{c['chapter_no']} {c['slug']} live={c['live']} held={c['held']} "
        f"empty_sol={c['empty_sol']} empty_tips={c['empty_tips']} short={c['live_short_of_printed']}"
    )

by = defaultdict(list)
for item in rep["hits"]:
    for h in item["hits"]:
        by[h.split(":")[0]].append(item)

print("\n=== real-looking ids ===")
for kind in (
    "empty-solution",
    "empty-tips",
    "sol-nested-frac",
    "stem-katex",
    "stem-smashed",
    "stem-junk",
    "bad-fig-key",
    "stem-fig-no-link",
):
    items = by.get(kind, [])
    print(f"\n{kind} n={len(items)}")
    for it in items[:20]:
        print(" ", it["label"], it["id"], it["hits"])

print("\n=== opt junk live ===")
for kind in sorted(k for k in by if "junk" in k):
    print(kind, len(by[kind]))
    for it in by[kind][:8]:
        print(" ", it["label"], it["id"], [h for h in it["hits"] if "junk" in h])

sb = p.supabase_client()
ids = []
for kind in ("empty-solution", "empty-tips", "sol-nested-frac", "stem-katex", "stem-smashed"):
    ids.extend(it["id"] for it in by.get(kind, []))
ids = list(dict.fromkeys(ids))
print(f"\nfetch {len(ids)} focus rows")
rows = []
for i in range(0, len(ids), 50):
    chunk = (
        sb.table("pyq_questions")
        .select("id,q_no,review_status,source_bbox,body,solution_md,tips_md,formulas_md")
        .in_("id", ids[i : i + 50])
        .execute()
        .data
        or []
    )
    rows.extend(chunk)
by_id = {r["id"]: r for r in rows}

print("\n--- empty sol ---")
for it in by.get("empty-solution", []):
    r = by_id[it["id"]]
    print(it["label"], r["review_status"], (r.get("source_bbox") or {}).get("pdf_q"))

print("\n--- empty tips ---")
for it in by.get("empty-tips", []):
    r = by_id[it["id"]]
    print(it["label"], r["id"], "sol_len", len(r.get("solution_md") or ""), "formulas", bool(r.get("formulas_md")))

print("\n--- nested frac snippets ---")
for it in by.get("sol-nested-frac", []):
    r = by_id[it["id"]]
    sol = r.get("solution_md") or ""
    m = NESTED_FRAC.search(sol)
    start = max(0, (m.start() if m else 0) - 80)
    print("\n", it["label"], it["id"])
    print(sol[start : start + 240].replace("\n", " | "))
    print(" smashed", smashed_tex(sol), "paper", "<!-- paper-ocr -->" in sol)

print("\n--- stem katex/smashed ---")
for it in by.get("stem-katex", []) + by.get("stem-smashed", []):
    r = by_id.get(it["id"])
    if not r:
        continue
    body = r.get("body") or ""
    print("\n", it["label"], r["review_status"], "len", len(body))
    print(body[:400].replace("\n", " | "))

# figures: collect keys from a sample of live questions via sql
print("\n--- figure keys in live bodies/sols (fresh query) ---")
chap_ids = [c["slug"] for c in rep["chapters"]]
# can't slug easily; query by ids of hits with fig
fig_keys = set()
sol_fig_q = 0
for item in rep["hits"][:1]:
    pass
# pull all live for these chapters isn't in json. Query links table.
links = (
    sb.table("pyq_figure_links")
    .select("question_id,role,figures:pyq_figures(figure_key,storage_path,public_url)")
    .limit(5)
    .execute()
    .data
)
print("sample links", json.dumps(links, default=str)[:800])
