#!/usr/bin/env python3
"""Phase 3 - resolve page-boundary artifacts on the Laws of Motion pages.
Deterministic. No AI, no cost."""
import json
import re

import pymupdf

import pyq_common as p

DATE_RE = re.compile(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(20\d{2})\s*\(([ME])\)")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
TOP_BAND_PT = 60.0
ORPHAN_TOP_PT = 60.0


def column_top_text(doc, page_no, column):
    """Text in the top 60 pt of one column of a 1-indexed page."""
    if page_no < 1 or page_no > len(doc):
        return ""
    page = doc[page_no - 1]
    width = page.rect.width
    mid = width / 2
    x0, x1 = (38.0, mid) if column == "L" else (mid, width - 18.0)
    return page.get_textbox(pymupdf.Rect(x0, 0.0, x1, TOP_BAND_PT))


def parse_date(text):
    m = DATE_RE.search(text or "")
    if not m:
        return None
    d, mon, y, shift = m.groups()
    if mon not in MONTHS:
        return None
    return (f"{y}-{MONTHS[mon]:02d}-{int(d):02d}",
            "morning" if shift == "M" else "evening")


def main():
    sb = p.supabase_client()
    doc = pymupdf.open(p.PDF_PATH)
    skeleton = p.load_skeleton()
    orphans = json.loads((p.OUT / "orphan_figures.json").read_text(encoding="utf-8"))

    ch5 = [r for r in skeleton if r["chapter_no"] == p.CHAPTER_5]
    undated = [r for r in ch5 if not r["exam_date"]]
    print(f"chapter 5 undated : {len(undated)}")

    fixes, unresolved = [], []
    for rec in undated:
        page, col = rec["page"], rec["column"]
        probes = [("next_page_same_column", page + 1, col)]
        if col == "L":
            probes.append(("same_page_next_column", page, "R"))
        else:
            probes.append(("next_page_left_column", page + 1, "L"))

        hit = None
        for rule, probe_page, probe_col in probes:
            parsed = parse_date(column_top_text(doc, probe_page, probe_col))
            if parsed:
                hit = (rule, probe_page, parsed)
                break

        if hit is None:
            unresolved.append({"kind": "date", "q_no": rec["q_no"],
                               "page": page, "column": col})
            continue

        rule, found_page, (date, shift) = hit
        fixes.append({"q_no": rec["q_no"], "page": page, "column": col,
                      "exam_date": date, "exam_shift": shift,
                      "found_on_page": found_page, "rule": rule})

    # orphan figures on chapter pages: last question of the same column, previous page
    orphan_fixes = []
    for orph in orphans:
        if orph["page"] not in p.CHAPTER_5_PAGES:
            continue
        if orph["bbox"][1] >= ORPHAN_TOP_PT:
            unresolved.append({"kind": "orphan", **orph, "why": "not at column top"})
            continue
        page_width = doc[orph["page"] - 1].rect.width
        col = "L" if orph["bbox"][0] < page_width / 2 else "R"
        prev = [r for r in ch5 if r["page"] == orph["page"] - 1 and r["column"] == col]
        if not prev:
            unresolved.append({"kind": "orphan", **orph,
                               "why": "no question in that column on the previous page"})
            continue
        owner = max(prev, key=lambda r: r["bbox"][1])
        orphan_fixes.append({"figure_key": orph["figure_key"], "page": orph["page"],
                             "owner_q_no": owner["q_no"], "owner_page": owner["page"],
                             "column": col, "rule": "orphan_top_of_column"})

    (p.OUT / "boundary_fixes.json").write_text(json.dumps(
        {"dates": fixes, "orphans": orphan_fixes}, indent=2), encoding="utf-8")
    (p.OUT / "manual_review.json").write_text(json.dumps(
        unresolved, indent=2), encoding="utf-8")

    ch5_id = sb.table("pyq_chapters").select("id").eq(
        "chapter_no", p.CHAPTER_5).execute().data[0]["id"]
    for fix in fixes:
        sb.table("pyq_questions").update(
            {"exam_date": fix["exam_date"], "exam_shift": fix["exam_shift"]}
        ).eq("chapter_id", ch5_id).eq("q_no", fix["q_no"]).execute()

    print(f"dates resolved    : {len(fixes)}")
    for fix in fixes:
        print(f"  Q{fix['q_no']} p{fix['page']}{fix['column']} -> "
              f"{fix['exam_date']} {fix['exam_shift']} via {fix['rule']}")
    print(f"orphans on 47-60  : "
          f"{len([o for o in orphans if o['page'] in p.CHAPTER_5_PAGES])}")
    print(f"orphans resolved  : {len(orphan_fixes)}")
    print(f"manual review     : {len(unresolved)}")


if __name__ == "__main__":
    main()
