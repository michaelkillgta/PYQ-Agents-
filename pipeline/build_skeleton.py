#!/usr/bin/env python3
"""
PHASE 1 — Build the structural skeleton. No AI. No cost.

Produces skeleton.json: one record per question with everything that can be
known with certainty from the PDF's own geometry and text layer.

    chapter / topic / tier / q_no / page / bbox / figures / exam date / shift
    / answer (from the book's answer key) / flags

Everything downstream treats this file as GROUND TRUTH and is forbidden
from changing it. The VLM only fills in `body` and `options`.

Usage:
    python build_skeleton.py book.pdf ./out
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

# --- font signatures, verified against this book -------------------------
CHAPTER_FONT = "FiraSans-ExtraBold"      # size ~20 "CHAPTER 2" / ~40 title
TIER_FONT    = "FiraSans-ExtraBold"      # size ~11.2 "CONCEPT BUILDER"
TOPIC_FONT   = "TimesNewRomanPS-BoldItal"  # size ~11.2 "Fundamentals of Vectors"

TIER_MAP = {
    "CONCEPT BUILDER": "concept_builder",
    "MUST DO": "must_do",
    "ADVANCED": "advanced",
}

Q_ANCHOR = re.compile(r"^Q(\d+)\s*([\.\*\^])")
DATE_RE  = re.compile(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(20\d{2})\s*\(([ME])\)")
CHAP_RE  = re.compile(r"^CHAPTER\s+(\d+)$")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

WATERMARK_COVER = 0.85
MIN_FIG_PT = 18
FOOTER_PT = 38          # page number band at the bottom
LEFT_MARGIN = 38


def line_text(line):
    return "".join(s["text"] for s in line["spans"]).strip()


def collect_page_marks(page):
    """Return chapter/tier/topic headings and question anchors, with geometry."""
    pw, ph = page.rect.width, page.rect.height
    mid = pw / 2
    marks = []
    chapter_no = None

    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            txt = line_text(line)
            if not txt:
                continue
            span = line["spans"][0]
            font, size = span["font"], span["size"]
            x0, y0 = line["bbox"][0], line["bbox"][1]
            col = "L" if x0 < mid else "R"

            m = CHAP_RE.match(txt)
            if m and font == CHAPTER_FONT and size > 15:
                chapter_no = int(m.group(1))
                continue

            if font == TIER_FONT and 10 < size < 13:
                key = next((k for k in TIER_MAP if txt.upper().startswith(k)), None)
                if key:
                    marks.append({"kind": "tier", "value": TIER_MAP[key],
                                  "col": col, "y": y0})
                    continue

            if font == TOPIC_FONT and 10 < size < 13:
                marks.append({"kind": "topic", "value": txt, "col": col, "y": y0})
                continue

            m = Q_ANCHOR.match(txt)
            if m:
                marks.append({
                    "kind": "question",
                    "q_no": int(m.group(1)),
                    "marker": m.group(2),      # '.' | '*' out-of-syllabus | '^' good-to-solve
                    "col": col, "y": y0, "x": x0,
                })

    # reading order: entire left column top->bottom, then entire right column
    marks.sort(key=lambda m: (m["col"] == "R", m["y"]))
    return marks, chapter_no


def page_figures(page):
    pw = page.rect.width
    out = []
    for info in page.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        if (x1 - x0) > WATERMARK_COVER * pw:
            continue
        if (x1 - x0) < MIN_FIG_PT or (y1 - y0) < MIN_FIG_PT:
            continue
        out.append({"xref": info["xref"], "bbox": (x0, y0, x1, y1)})
    return out


def build(pdf_path, out_dir):
    doc = pymupdf.open(pdf_path)
    answer_key = json.loads((Path(out_dir) / "answer_key.json").read_text())

    records = []
    cur_chapter = None
    cur_tier = None
    cur_topic = None
    orphan_figs = []

    for pno in range(len(doc)):
        page = doc[pno]
        pw, ph = page.rect.width, page.rect.height
        mid = pw / 2

        marks, chap = collect_page_marks(page)
        if chap:
            cur_chapter = chap
            cur_tier = None          # tier resets at each chapter
            cur_topic = None
        if cur_chapter is None:
            continue                 # front matter
        if not any(m["kind"] == "question" for m in marks):
            continue                 # trend page / answer keys

        figs = page_figures(page)
        q_marks = [m for m in marks if m["kind"] == "question"]

        # question bbox: from its anchor down to the next anchor in the SAME column
        segs = []
        for i, qm in enumerate(q_marks):
            later = [m for m in q_marks[i + 1:] if m["col"] == qm["col"]]
            y_end = later[0]["y"] if later else ph - FOOTER_PT
            x0, x1 = (LEFT_MARGIN, mid) if qm["col"] == "L" else (mid, pw - 18)
            segs.append((qm, (x0, qm["y"] - 5, x1, y_end - 2)))

        # walk marks in reading order so tier/topic carry forward correctly
        seg_by_q = {id(qm): bbox for qm, bbox in segs}
        for m in marks:
            if m["kind"] == "tier":
                cur_tier = m["value"]
                continue
            if m["kind"] == "topic":
                cur_topic = m["value"]
                continue

            bbox = seg_by_q[id(m)]
            text = page.get_textbox(pymupdf.Rect(*bbox))

            exam_date = exam_shift = None
            dm = DATE_RE.search(text)
            if dm:
                d, mon, y, sh = dm.groups()
                if mon in MONTHS:
                    exam_date = f"{y}-{MONTHS[mon]:02d}-{int(d):02d}"
                    exam_shift = "morning" if sh == "M" else "evening"

            owned = [f for f in figs
                     if f["bbox"][0] >= bbox[0] - 8 and f["bbox"][2] <= bbox[2] + 8
                     and f["bbox"][1] >= bbox[1] - 8 and f["bbox"][3] <= bbox[3] + 8]

            ans = (answer_key.get(str(cur_chapter), {})
                             .get("answers", {})
                             .get(str(m["q_no"])))

            records.append({
                "chapter_no": cur_chapter,
                "chapter_title": answer_key.get(str(cur_chapter), {}).get("title"),
                "topic": cur_topic,
                "tier": cur_tier,
                "q_no": m["q_no"],
                "page": pno + 1,
                "column": m["col"],
                "bbox": [round(v, 1) for v in bbox],
                "figure_keys": [f"p{pno + 1:03d}_x{f['xref']}" for f in owned],
                "exam_date": exam_date,
                "exam_shift": exam_shift,
                "out_of_syllabus": m["marker"] == "*",
                "good_to_solve": m["marker"] == "^",
                "answer_type": ans["type"] if ans else None,
                "answer_value": ans["value"] if ans else None,
                # filled by Phase 2 — never by this script
                "body": None,
                "options": None,
                "review_status": "skeleton_only",
            })

        used = {x for r in records if r["page"] == pno + 1 for x in r["figure_keys"]}
        for f in figs:
            k = f"p{pno + 1:03d}_x{f['xref']}"
            if k not in used:
                orphan_figs.append({"figure_key": k, "page": pno + 1,
                                    "bbox": [round(v, 1) for v in f["bbox"]]})

    out = Path(out_dir)
    (out / "skeleton.json").write_text(json.dumps(records, indent=1))
    (out / "orphan_figures.json").write_text(json.dumps(orphan_figs, indent=1))

    # ---- reconciliation against the book's own answer key ----
    expected = {int(c): len(v["answers"]) for c, v in answer_key.items()}
    got = {}
    for r in records:
        got[r["chapter_no"]] = got.get(r["chapter_no"], 0) + 1

    bad = [(c, expected[c], got.get(c, 0)) for c in sorted(expected)
           if expected[c] != got.get(c, 0)]

    print(f"questions in skeleton : {len(records)}")
    print(f"answer key total      : {sum(expected.values())}")
    print(f"chapters mismatching  : {len(bad)}  {bad[:6]}")
    print(f"with tier             : {sum(1 for r in records if r['tier'])}")
    print(f"with topic            : {sum(1 for r in records if r['topic'])}")
    print(f"with exam date        : {sum(1 for r in records if r['exam_date'])}")
    print(f"with answer attached  : {sum(1 for r in records if r['answer_value'])}")
    print(f"with >=1 figure       : {sum(1 for r in records if r['figure_keys'])}")
    print(f"orphan figures        : {len(orphan_figs)}")
    return records


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "./out")
