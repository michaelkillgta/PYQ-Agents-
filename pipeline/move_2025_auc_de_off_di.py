#!/usr/bin/env python3
"""Move 2025 AUC/DE rows off Definite Integration onto their catalog chapters."""
from __future__ import annotations

import sys

import pyq_common as p

DI_NO = 17
AUC_NO = 18
DE_NO = 19
SUBJECT = "Mathematics"


def section_of(bbox: dict) -> str | None:
    raw = str((bbox or {}).get("chapter") or "").strip().lower()
    if raw in {"auc", "area under curves"}:
        return "auc"
    if raw in {"de", "differential equations"}:
        return "de"
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sb = p.supabase_client()
    di_id = p.resolve_chapter_id(sb, DI_NO, SUBJECT)
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
    unit_id = sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data[0]["id"]

    def ensure_chapter(no: int, name: str, slug: str) -> int:
        existing = (
            sb.table("pyq_chapters")
            .select("id")
            .eq("unit_id", unit_id)
            .eq("chapter_no", no)
            .execute()
            .data
            or []
        )
        if existing:
            return existing[0]["id"]
        rec = (
            sb.table("pyq_chapters")
            .insert({
                "unit_id": unit_id,
                "chapter_no": no,
                "name": name,
                "catalog_slug": slug,
            })
            .execute()
            .data
        )
        return rec[0]["id"]

    auc_id = ensure_chapter(AUC_NO, "Area Under Curves", "area-under-curves")
    de_id = ensure_chapter(DE_NO, "Differential Equations", "differential-equations")
    print(f"di={di_id} auc={auc_id} de={de_id}", flush=True)

    rows = (
        sb.table("pyq_questions")
        .select("id,q_no,chapter_id,exam_date,source_bbox")
        .eq("chapter_id", di_id)
        .execute()
        .data
        or []
    )
    buckets = {"auc": [], "de": []}
    stay = 0
    for row in rows:
        bbox = row.get("source_bbox") if isinstance(row.get("source_bbox"), dict) else {}
        booklet = str(bbox.get("booklet") or "")
        if not booklet.startswith("2025"):
            stay += 1
            continue
        sec = section_of(bbox)
        if sec is None:
            stay += 1
            continue
        buckets[sec].append(row)

    dest = {"auc": auc_id, "de": de_id}
    moved = 0
    for sec, group in buckets.items():
        group.sort(key=lambda r: (
            str((r.get("source_bbox") or {}).get("booklet")),
            int((r.get("source_bbox") or {}).get("pdf_q") or r["q_no"]),
        ))
        for i, row in enumerate(group, start=1):
            sb.table("pyq_questions").update({
                "chapter_id": dest[sec],
                "q_no": i,
            }).eq("id", row["id"]).execute()
            moved += 1
            bbox = row.get("source_bbox") or {}
            print(
                f"  move {bbox.get('booklet')} {sec} pdf_q={bbox.get('pdf_q')} "
                f"-> ch{dest[sec]} q_no={i}",
                flush=True,
            )
    print(f"moved {moved} stay_on_di {stay}", flush=True)
    for cid, label in ((di_id, "di"), (auc_id, "auc"), (de_id, "de")):
        n = len(
            sb.table("pyq_questions").select("id").eq("chapter_id", cid).execute().data or []
        )
        y = 0
        for r in sb.table("pyq_questions").select("exam_date,source_bbox").eq("chapter_id", cid).execute().data or []:
            bbox = r.get("source_bbox") if isinstance(r.get("source_bbox"), dict) else {}
            date = str(r.get("exam_date") or "")
            if date.startswith("2025") or str(bbox.get("booklet") or "").startswith("2025"):
                y += 1
        print(f"  {label} total={n} y2025={y}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
