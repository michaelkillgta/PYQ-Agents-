#!/usr/bin/env python3
"""Ingest Mathematics PDF chapter 2 (Quadratic Equation) into pyq_*.

Writes to ./out-math only. Does not touch Physics ./out.
"""
from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path

import pymupdf

import pyq_common as p
from build_skeleton import (
    DATE_RE,
    FOOTER_PT,
    LEFT_MARGIN,
    MONTHS,
    collect_page_marks,
    page_figures,
)
from extract_assets import extract_answer_key
from parse_ocr_page import parse_digitise_to_questions
from write_and_publish import options_publishable

PDF = Path(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
OUT = Path(r"c:\Users\tempo\Downloads\files\out-math")
CHAPTER = 2
CATALOG_SLUG = "quadratic-equation"
FIGURE_PREFIX = "math/figures"
PAGE_LO, PAGE_HI = 6, 13  # inclusive PDF pages (title 6, questions 7–13)
MIN_VEC_AREA = 180
MAX_VEC_AREA = 2800
DPI = 200


def configure_out():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)
    (OUT / "ocr").mkdir(exist_ok=True)
    (OUT / "extracted" / "pass1").mkdir(parents=True, exist_ok=True)
    p.OUT = OUT


def rasterize_pages(doc, pages: list[int]):
    zoom = DPI / 72
    mat = pymupdf.Matrix(zoom, zoom)
    for pno in pages:
        pix = doc[pno - 1].get_pixmap(matrix=mat)
        pix.save(str(OUT / "pages" / f"page_{pno:03d}.png"))


def extract_rasters(doc, pages: list[int]) -> list[dict]:
    manifest = []
    for pno in pages:
        page = doc[pno - 1]
        pw, ph = page.rect.width, page.rect.height
        mid = pw / 2
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            w, h = x1 - x0, y1 - y0
            if w > 0.85 * pw and h > 0.85 * ph:
                continue
            if w < 18 or h < 18:
                continue
            xref = info["xref"]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:
                pix = pymupdf.Pixmap(pix, 0)
            key = f"p{pno:03d}_x{xref}"
            pix.save(str(OUT / "figures" / f"{key}.png"))
            manifest.append({
                "figure_key": key,
                "file": f"figures/{key}.png",
                "page": pno,
                "bbox": [round(v, 1) for v in (x0, y0, x1, y1)],
                "column": "left" if x0 < mid else "right",
                "px_width": pix.width,
                "px_height": pix.height,
                "bytes": len(pix.tobytes("png")),
            })
    return manifest


def vector_crops(doc, records: list[dict]) -> list[dict]:
    """Render figure-sized vector clusters inside a question bbox (new-book suffix _v)."""
    extra = []
    zoom = DPI / 72
    mat = pymupdf.Matrix(zoom, zoom)
    for rec in records:
        page = doc[rec["page"] - 1]
        qb = pymupdf.Rect(*rec["bbox"])
        rects = []
        for d in page.get_drawings():
            r = d.get("rect")
            if r is None:
                continue
            area = abs(r.width * r.height)
            if area < MIN_VEC_AREA or area > MAX_VEC_AREA:
                continue
            if r.intersects(qb):
                rects.append(pymupdf.Rect(r))
        if not rects:
            continue
        union = rects[0]
        for r in rects[1:]:
            union |= r
        union = (union & qb) + (-4, -4, 4, 4)
        if union.is_empty or union.width < 20 or union.height < 20:
            continue
        if union.width * union.height > 0.55 * qb.width * qb.height:
            continue
        key = f"p{rec['page']:03d}_v{rec['q_no']}"
        pix = page.get_pixmap(matrix=mat, clip=union, alpha=False)
        dest = OUT / "figures" / f"{key}.png"
        pix.save(str(dest))
        rec["figure_keys"] = list(dict.fromkeys([*rec["figure_keys"], key]))
        extra.append({
            "figure_key": key,
            "file": f"figures/{key}.png",
            "page": rec["page"],
            "bbox": [round(v, 1) for v in (union.x0, union.y0, union.x1, union.y1)],
            "column": rec["column"],
            "px_width": pix.width,
            "px_height": pix.height,
            "bytes": dest.stat().st_size,
        })
    return extra


def build_chapter_skeleton(doc, key: dict) -> list[dict]:
    records = []
    cur_chapter = None
    cur_tier = None
    cur_topic = None
    for pno in range(PAGE_LO, PAGE_HI + 1):
        page = doc[pno - 1]
        pw, ph = page.rect.width, page.rect.height
        mid = pw / 2
        marks, chap = collect_page_marks(page)
        if chap:
            cur_chapter = chap
            cur_tier = None
            cur_topic = None
        if cur_chapter != CHAPTER:
            continue
        if not any(m["kind"] == "question" for m in marks):
            continue
        figs = page_figures(page)
        q_marks = [m for m in marks if m["kind"] == "question"]
        segs = []
        for i, qm in enumerate(q_marks):
            later = [m for m in q_marks[i + 1:] if m["col"] == qm["col"]]
            y_end = later[0]["y"] if later else ph - FOOTER_PT
            x0, x1 = (LEFT_MARGIN, mid) if qm["col"] == "L" else (mid, pw - 18)
            segs.append((qm, (x0, qm["y"] - 5, x1, y_end - 2)))
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
                    exam_shift = "morning" if sh in {"M", "F"} else "evening"
            owned = [f for f in figs
                     if f["bbox"][0] >= bbox[0] - 8 and f["bbox"][2] <= bbox[2] + 8
                     and f["bbox"][1] >= bbox[1] - 8 and f["bbox"][3] <= bbox[3] + 8]
            ans = (key.get(str(CHAPTER), {}).get("answers", {}).get(str(m["q_no"])))
            if ans is None:
                ans = (key.get(CHAPTER, {}).get("answers", {}).get(m["q_no"]))
            records.append({
                "chapter_no": CHAPTER,
                "chapter_title": key.get(str(CHAPTER), key.get(CHAPTER, {})).get("title"),
                "topic": cur_topic,
                "tier": cur_tier,
                "q_no": m["q_no"],
                "page": pno,
                "column": m["col"],
                "bbox": [round(v, 1) for v in bbox],
                "figure_keys": [f"p{pno:03d}_x{f['xref']}" for f in owned],
                "exam_date": exam_date,
                "exam_shift": exam_shift,
                "out_of_syllabus": m["marker"] == "*",
                "good_to_solve": m["marker"] == "^",
                "answer_type": ans["type"] if ans else None,
                "answer_value": ans["value"] if ans else None,
                "body": None,
                "options": None,
                "review_status": "skeleton_only",
            })
    return records


def seed_and_load(skeleton: list[dict], key: dict, manifest: list[dict]):
    sb = p.supabase_client()
    answers = key.get(str(CHAPTER)) or key.get(CHAPTER)
    if isinstance(answers, dict) and "answers" in answers:
        expected = len(answers["answers"])
        title = answers["title"]
    else:
        expected = 130
        title = "Quadratic Equation"

    subject = sb.table("pyq_subjects").upsert(
        {"name": "Mathematics"}, on_conflict="name").execute().data[0]
    unit = sb.table("pyq_units").upsert(
        {"subject_id": subject["id"],
         "name": "JEE Main Mathematics (MathonGo PYQ)",
         "sort_order": 2},
        on_conflict="subject_id,name").execute().data[0]
    chapter = sb.table("pyq_chapters").upsert({
        "unit_id": unit["id"],
        "chapter_no": CHAPTER,
        "name": title,
        "expected_question_count": expected,
        "catalog_slug": CATALOG_SLUG,
    }, on_conflict="unit_id,chapter_no").execute().data[0]
    chapter_id = chapter["id"]

    seen = []
    for rec in skeleton:
        if rec["topic"] and rec["topic"] not in seen:
            seen.append(rec["topic"])
    topic_rows = [{"chapter_id": chapter_id, "name": name, "sort_order": i}
                  for i, name in enumerate(seen)]
    if topic_rows:
        sb.table("pyq_topics").upsert(topic_rows, on_conflict="chapter_id,name").execute()
    topics = {(t["chapter_id"], t["name"]): t["id"] for t in
              sb.table("pyq_topics").select("id,chapter_id,name")
              .eq("chapter_id", chapter_id).execute().data}

    rows = []
    missing_tier = 0
    for rec in skeleton:
        if not rec["tier"]:
            missing_tier += 1
            rec["tier"] = "must_do"
        mcq = rec["answer_type"] == "mcq"
        rows.append({
            "chapter_id": chapter_id,
            "topic_id": topics.get((chapter_id, rec["topic"])),
            "q_no": rec["q_no"],
            "tier": rec["tier"],
            "format": "mcq" if mcq else "numerical",
            "body": None,
            "correct_option": int(rec["answer_value"]) if mcq and rec["answer_value"] else None,
            "numerical_answer": None if mcq else rec["answer_value"],
            "exam_date": rec["exam_date"],
            "exam_shift": rec["exam_shift"],
            "out_of_syllabus": rec["out_of_syllabus"],
            "good_to_solve": rec["good_to_solve"],
            "source_page": rec["page"],
            "source_bbox": rec["bbox"],
            "review_status": "skeleton_only",
        })
    sb.table("pyq_questions").upsert(rows, on_conflict="chapter_id,q_no").execute()
    print(f"seeded chapter_id={chapter_id} questions={len(rows)} missing_tier_filled={missing_tier}")

    if manifest:
        fig_rows = []
        for meta in manifest:
            key = meta["figure_key"]
            local = OUT / "figures" / f"{key}.png"
            object_name = f"{FIGURE_PREFIX}/{key}.png"
            sb.storage.from_(p.BUCKET).upload(
                object_name,
                local.read_bytes(),
                {"content-type": mimetypes.guess_type(local.name)[0] or "image/png",
                 "upsert": "true"},
            )
            fig_rows.append({
                "figure_key": key,
                "storage_path": f"{p.BUCKET}/{object_name}",
                "public_url": sb.storage.from_(p.BUCKET).get_public_url(object_name),
                "px_width": meta["px_width"],
                "px_height": meta["px_height"],
                "bytes": meta["bytes"],
                "checksum": p.sha256_file(local),
                "source_page": meta["page"],
                "source_bbox": meta["bbox"],
            })
        sb.table("pyq_figures").upsert(fig_rows, on_conflict="figure_key").execute()
        print(f"figures uploaded : {len(fig_rows)}")

        q_ids = {q["q_no"]: q["id"] for q in sb.table("pyq_questions")
                 .select("id,q_no").eq("chapter_id", chapter_id).execute().data}
        fig_ids = {f["figure_key"]: f["id"] for f in
                   sb.table("pyq_figures").select("id,figure_key").execute().data}
        links = []
        for rec in skeleton:
            for order, fkey in enumerate(rec["figure_keys"]):
                if fkey not in fig_ids:
                    continue
                links.append({
                    "figure_id": fig_ids[fkey],
                    "question_id": q_ids[rec["q_no"]],
                    "option_id": None,
                    "role": "question_body",
                    "sort_order": order,
                })
        existing = {(l["figure_id"], l["question_id"]) for l in sb.table("pyq_figure_links")
                    .select("figure_id,question_id").execute().data}
        fresh = [l for l in links if (l["figure_id"], l["question_id"]) not in existing]
        if fresh:
            sb.table("pyq_figure_links").insert(fresh).execute()
        print(f"figure links     : {len(links)} new={len(fresh)}")
    return chapter_id


def ocr_and_publish(skeleton: list[dict], chapter_id: int):
    env = p.load_env()
    pages = sorted({r["page"] for r in skeleton})
    parsed, failures = {}, {}
    out_dir = OUT / "extracted" / "pass1"
    for page_no in pages:
        slice_ = [s for s in skeleton if s["page"] == page_no]
        allowed_q = {s["q_no"] for s in slice_}
        allowed_f = {k for s in slice_ for k in s["figure_keys"]}
        try:
            digitise = p.digitise_page(page_no, env["SARVAM_API_KEY"])
            questions = parse_digitise_to_questions(digitise, slice_)
            p.validate_page_response({"questions": questions}, allowed_q, allowed_f)
            (out_dir / f"page_{page_no:03d}.json").write_text(
                json.dumps({"questions": questions}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            for q in questions:
                parsed[str(q["q_no"])] = {"body": q["body"], "options": q.get("options"),
                                          "page": page_no}
            print(f"page {page_no} ok  q={len(questions)}")
        except Exception as exc:
            failures[str(page_no)] = f"{type(exc).__name__}: {exc}"
            print(f"page {page_no} failed - {failures[str(page_no)]}")

    (out_dir / "parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    sb = p.supabase_client()
    q_ids = {str(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", chapter_id).execute().data}
    spec_by = {str(r["q_no"]): r for r in skeleton}
    option_rows, publishable, skipped = [], [], []
    for q_no, entry in parsed.items():
        spec = spec_by[q_no]
        body = (entry.get("body") or "").strip()
        options = entry.get("options")
        mcq = spec["answer_type"] == "mcq"
        shape_ok = (not mcq and options is None) or (mcq and options_publishable(options))
        missed = not body or body.startswith("(OCR missed")
        if missed or not shape_ok:
            skipped.append({"q_no": int(q_no), "mcq": mcq, "missed": missed,
                            "n_opts": None if options is None else len(options)})
            status = "unreviewed"
        else:
            status = "auto_ok"
            publishable.append(int(q_no))
        sb.table("pyq_questions").update({
            "body": body or None,
            "extraction_confidence": 0.5,
            "review_status": status,
        }).eq("id", q_ids[q_no]).execute()
        if options:
            for i, text in enumerate(options, start=1):
                option_rows.append({
                    "question_id": q_ids[q_no],
                    "option_index": i,
                    "body": text,
                })
    if option_rows:
        sb.table("pyq_question_options").upsert(
            option_rows, on_conflict="question_id,option_index").execute()
    print(f"parsed={len(parsed)} published={len(publishable)} held={len(skipped)} "
          f"failed_pages={sorted(failures)}")
    if skipped:
        print("held:", sorted(skipped, key=lambda x: x["q_no"]))


def main():
    configure_out()
    p.load_env()
    doc = pymupdf.open(PDF)
    key = extract_answer_key(doc, start_hint=300)
    # keys may be int or str depending on json roundtrip later
    (OUT / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    ch = key.get(CHAPTER) or key.get(str(CHAPTER))
    print(f"answer key ch2 : {ch['title'] if ch else None} n={len(ch['answers']) if ch else 0}")

    pages = list(range(PAGE_LO, PAGE_HI + 1))
    rasterize_pages(doc, pages)
    print(f"rasters : {len(pages)} pages")

    manifest = extract_rasters(doc, pages)
    records = build_chapter_skeleton(doc, key)
    vec = vector_crops(doc, records)
    manifest.extend(vec)
    (OUT / "figures.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT / "skeleton.json").write_text(json.dumps(records, indent=1), encoding="utf-8")
    print(f"skeleton : {len(records)} with_fig={sum(1 for r in records if r['figure_keys'])} "
          f"rasters={len(manifest) - len(vec)} vector_crops={len(vec)}")

    expected = len((ch or {}).get("answers") or {})
    got = len(records)
    if got != expected:
        print(f"COUNT MISMATCH skeleton={got} key={expected}")
    chapter_id = seed_and_load(records, key, manifest)
    ocr_and_publish(records, chapter_id)


if __name__ == "__main__":
    main()
