#!/usr/bin/env python3
"""OCR the whole Mathematics MathonGo PYQ book into pyq_*.

Writes only to ./out-math. Resumes cached digitise JSON. Does not touch Physics ./out.
"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import pymupdf

import pyq_common as p
from build_skeleton import build as build_skeleton
from extract_assets import extract_answer_key, extract_figures
from parse_ocr_page import parse_digitise_to_questions
from write_and_publish import options_publishable

PDF = Path(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
OUT = Path(r"c:\Users\tempo\Downloads\files\out-math")
FIGURE_PREFIX = "math/figures"
DPI = 200

CATALOG_SLUG = {
    1: "basic-of-mathematics",
    2: "quadratic-equation",
    3: "complex-number",
    4: "sequences-and-series",
    5: "permutation-combination",
    6: "binomial-theorem",
    7: "mathematical-reasoning",
    8: "statistics",
    9: "matrices",
    10: "determinants",
    11: "probability",
    12: "sets-and-relations",
    13: "functions",
    14: "limits",
    15: "continuity-and-differentiability",
    16: "differentiation",
    17: "application-of-derivatives",
    18: "indefinite-integration",
    19: "definite-integration",
    20: "area-under-curves",
    21: "differential-equations",
    22: "straight-lines",
    23: "circle",
    24: "parabola",
    25: "ellipse",
    26: "hyperbola",
    27: "trigonometric-ratios-and-identities",
    28: "trigonometric-equations",
    29: "inverse-trigonometric-functions",
    30: "trigonometric-ratios-and-identities",
    31: "trigonometric-ratios-and-identities",
    32: "vector-algebra",
    33: "three-dimensional-geometry",
}


def paged(make_query, size=1000):
    rows = []
    start = 0
    while True:
        batch = make_query().range(start, start + size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < size:
            break
        start += size
    return rows


def configure_out():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ocr").mkdir(exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)
    (OUT / "extracted" / "pass1").mkdir(parents=True, exist_ok=True)
    p.OUT = OUT


def rasterize_question_pages(doc, pages: list[int]):
    zoom = DPI / 72
    mat = pymupdf.Matrix(zoom, zoom)
    wrote = 0
    for pno in pages:
        dest = OUT / "pages" / f"page_{pno:03d}.png"
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        pix = doc[pno - 1].get_pixmap(matrix=mat)
        pix.save(str(dest))
        wrote += 1
    return wrote


def seed_and_load(skeleton: list[dict], key: dict, manifest: list[dict]):
    sb = p.supabase_client()
    subject = sb.table("pyq_subjects").upsert(
        {"name": "Mathematics"}, on_conflict="name").execute().data[0]
    unit = sb.table("pyq_units").upsert(
        {"subject_id": subject["id"],
         "name": "JEE Main Mathematics (MathonGo PYQ)",
         "sort_order": 2},
        on_conflict="subject_id,name").execute().data[0]

    chapter_rows = []
    for raw_no, entry in key.items():
        chapter_no = int(raw_no)
        chapter_rows.append({
            "unit_id": unit["id"],
            "chapter_no": chapter_no,
            "name": entry["title"],
            "expected_question_count": len(entry["answers"]),
            "catalog_slug": CATALOG_SLUG[chapter_no],
        })
    chapter_rows.sort(key=lambda r: r["chapter_no"])
    sb.table("pyq_chapters").upsert(
        chapter_rows, on_conflict="unit_id,chapter_no").execute()
    chapters = {c["chapter_no"]: c["id"] for c in
                sb.table("pyq_chapters").select("id,chapter_no")
                .eq("unit_id", unit["id"]).execute().data}

    seen = {}
    for rec in skeleton:
        pair = (rec["chapter_no"], rec["topic"])
        if rec["topic"] and pair not in seen:
            seen[pair] = len(seen)
    topic_rows = []
    per_chapter = {}
    for (chapter_no, name) in seen:
        order = per_chapter.get(chapter_no, 0)
        per_chapter[chapter_no] = order + 1
        topic_rows.append({
            "chapter_id": chapters[chapter_no],
            "name": name,
            "sort_order": order,
        })
    if topic_rows:
        sb.table("pyq_topics").upsert(topic_rows, on_conflict="chapter_id,name").execute()
    math_ids = set(chapters.values())
    topics = {(t["chapter_id"], t["name"]): t["id"] for t in paged(
        lambda: sb.table("pyq_topics").select("id,chapter_id,name")
    ) if t["chapter_id"] in math_ids}

    ids = list(chapters.values())
    existing = {(r["chapter_id"], r["q_no"]) for r in paged(
        lambda: sb.table("pyq_questions").select("chapter_id,q_no").in_("chapter_id", ids)
    )}
    rows = []
    missing_tier = 0
    last_tier = "must_do"
    for rec in skeleton:
        if rec["tier"]:
            last_tier = rec["tier"]
        else:
            missing_tier += 1
            rec["tier"] = last_tier
        chapter_id = chapters[rec["chapter_no"]]
        if (chapter_id, rec["q_no"]) in existing:
            continue
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
    BATCH = 400
    for i in range(0, len(rows), BATCH):
        sb.table("pyq_questions").upsert(
            rows[i:i + BATCH], on_conflict="chapter_id,q_no").execute()
    print(f"seeded new={len(rows)} already={len(existing)} chapters={len(chapters)} "
          f"missing_tier_filled={missing_tier}")

    if manifest:
        fig_rows = []
        uploaded = set()
        for meta in manifest:
            fkey = meta["figure_key"]
            local = OUT / "figures" / f"{fkey}.png"
            if not local.exists():
                continue
            object_name = f"{FIGURE_PREFIX}/{fkey}.png"
            if fkey not in uploaded:
                sb.storage.from_(p.BUCKET).upload(
                    object_name,
                    local.read_bytes(),
                    {"content-type": mimetypes.guess_type(local.name)[0] or "image/png",
                     "upsert": "true"},
                )
                uploaded.add(fkey)
            fig_rows.append({
                "figure_key": fkey,
                "storage_path": f"{p.BUCKET}/{object_name}",
                "public_url": sb.storage.from_(p.BUCKET).get_public_url(object_name),
                "px_width": meta["px_width"],
                "px_height": meta["px_height"],
                "bytes": meta["bytes"],
                "checksum": p.sha256_file(local),
                "source_page": meta["page"],
                "source_bbox": meta["bbox"],
            })
        if fig_rows:
            sb.table("pyq_figures").upsert(fig_rows, on_conflict="figure_key").execute()
        print(f"figures uploaded : {len(uploaded)}")

        q_rows = paged(lambda: sb.table("pyq_questions").select("id,q_no,chapter_id")
                       .in_("chapter_id", list(chapters.values())))
        q_ids = {(r["chapter_id"], r["q_no"]): r["id"] for r in q_rows}
        fig_ids = {f["figure_key"]: f["id"] for f in
                   sb.table("pyq_figures").select("id,figure_key").execute().data}
        links = []
        for rec in skeleton:
            cid = chapters[rec["chapter_no"]]
            qid = q_ids.get((cid, rec["q_no"]))
            if not qid:
                continue
            for order, fkey in enumerate(rec["figure_keys"]):
                if fkey not in fig_ids:
                    continue
                links.append({
                    "figure_id": fig_ids[fkey],
                    "question_id": qid,
                    "option_id": None,
                    "role": "question_body",
                    "sort_order": order,
                })
        existing = {(l["figure_id"], l["question_id"]) for l in
                    sb.table("pyq_figure_links").select("figure_id,question_id").execute().data}
        fresh = [l for l in links if (l["figure_id"], l["question_id"]) not in existing]
        if fresh:
            for i in range(0, len(fresh), 400):
                sb.table("pyq_figure_links").insert(fresh[i:i + 400]).execute()
        print(f"figure links     : {len(links)} new={len(fresh)}")
    return chapters


def ocr_all(skeleton: list[dict]):
    env = p.load_env()
    pages = sorted({r["page"] for r in skeleton})
    parsed = {}
    failures = {}
    out_dir = OUT / "extracted" / "pass1"
    by_page = {}
    for rec in skeleton:
        by_page.setdefault(rec["page"], []).append(rec)

    for i, page_no in enumerate(pages, start=1):
        slice_ = by_page[page_no]
        allowed_q = {s["q_no"] for s in slice_}
        allowed_f = {k for s in slice_ for k in s["figure_keys"]}
        try:
            digitise = p.digitise_page(page_no, env["SARVAM_API_KEY"])
            questions = parse_digitise_to_questions(digitise, slice_)
            p.validate_page_response({"questions": questions}, allowed_q, allowed_f)
            (out_dir / f"page_{page_no:03d}.json").write_text(
                json.dumps({"questions": questions}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            chapter_no = slice_[0]["chapter_no"]
            for q in questions:
                parsed[f"{chapter_no}:{q['q_no']}"] = {
                    "body": q["body"],
                    "options": q.get("options"),
                    "page": page_no,
                    "chapter_no": chapter_no,
                    "q_no": q["q_no"],
                }
            print(f"[{i}/{len(pages)}] page {page_no} ok  q={len(questions)}", flush=True)
        except Exception as exc:
            failures[str(page_no)] = f"{type(exc).__name__}: {exc}"
            print(f"[{i}/{len(pages)}] page {page_no} FAILED {failures[str(page_no)]}", flush=True)
        if i % 20 == 0:
            (out_dir / "parsed.json").write_text(
                json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    (out_dir / "parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
    print(f"ocr pages ok={len(pages) - len(failures)}/{len(pages)} parsed={len(parsed)}")
    return parsed, failures


def publish(skeleton: list[dict], parsed: dict, chapters: dict):
    sb = p.supabase_client()
    spec_by = {(r["chapter_no"], r["q_no"]): r for r in skeleton}
    q_rows = paged(lambda: sb.table("pyq_questions").select("id,q_no,chapter_id")
                   .in_("chapter_id", list(chapters.values())))
    q_ids = {(r["chapter_id"], r["q_no"]): r["id"] for r in q_rows}

    option_rows, publishable, skipped = [], [], []
    for key, entry in parsed.items():
        chapter_no, q_no = entry["chapter_no"], entry["q_no"]
        spec = spec_by[(chapter_no, q_no)]
        cid = chapters[chapter_no]
        qid = q_ids[(cid, q_no)]
        body = (entry.get("body") or "").strip()
        options = entry.get("options")
        mcq = spec["answer_type"] == "mcq"
        shape_ok = (not mcq and options is None) or (mcq and options_publishable(options))
        missed = not body or body.startswith("(OCR missed")
        if missed or not shape_ok:
            skipped.append({"chapter": chapter_no, "q_no": q_no, "mcq": mcq,
                            "missed": missed,
                            "n_opts": None if options is None else len(options)})
            status = "unreviewed"
        else:
            status = "auto_ok"
            publishable.append((chapter_no, q_no))
        sb.table("pyq_questions").update({
            "body": body or None,
            "extraction_confidence": 0.5,
            "review_status": status,
        }).eq("id", qid).execute()
        if options:
            for i, text in enumerate(options, start=1):
                option_rows.append({
                    "question_id": qid,
                    "option_index": i,
                    "body": text,
                })
    if option_rows:
        for i in range(0, len(option_rows), 400):
            sb.table("pyq_question_options").upsert(
                option_rows[i:i + 400], on_conflict="question_id,option_index").execute()
    print(f"published={len(publishable)} held={len(skipped)} options={len(option_rows)}")
    (OUT / "extracted" / "pass1" / "held.json").write_text(
        json.dumps(skipped, indent=1), encoding="utf-8")


def main():
    configure_out()
    p.load_env()
    doc = pymupdf.open(PDF)
    key = extract_answer_key(doc, start_hint=300)
    (OUT / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"answer key chapters={len(key)} n={sum(len(v['answers']) for v in key.values())}")

    build_skeleton(str(PDF), str(OUT))
    skeleton = p.load_skeleton()
    pages = sorted({r["page"] for r in skeleton})
    print(f"question pages : {len(pages)}")

    manifest = extract_figures(doc, OUT)
    (OUT / "figures.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"raster figures : {len(manifest)}")

    wrote = rasterize_question_pages(doc, pages)
    print(f"page rasters wrote : {wrote} (rest cached)")

    chapters = seed_and_load(skeleton, key, manifest)
    parsed, failures = ocr_all(skeleton)
    publish(skeleton, parsed, chapters)
    if failures:
        print("failed pages:", sorted(int(x) for x in failures))


if __name__ == "__main__":
    main()
