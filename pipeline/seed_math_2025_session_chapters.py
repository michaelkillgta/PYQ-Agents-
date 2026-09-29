#!/usr/bin/env python3
"""Create Mathematics pyq_chapters 1–29 to match the 2025 Jan/Apr chapter-wise TOC.

Renumbers existing DI/AUC/DE rows (19/20/21 → 17/18/19) without moving questions
off those chapter_ids. Inserts missing chapters. Does not ingest stems.
"""
from __future__ import annotations

import sys

import pyq_common as p

SUBJECT = "Mathematics"
# Printed Q counts from the January 2025 chapter-wise bank (inventory gate).
JAN_2025_COUNTS = {
    1: 1,
    2: 6,
    3: 10,
    4: 16,
    5: 10,
    6: 11,
    7: 4,
    8: 10,
    9: 8,
    10: 13,
    11: 11,
    12: 14,
    13: 6,
    14: 6,
    15: 4,
    16: 5,
    17: 13,
    18: 12,
    19: 12,
    20: 10,
    21: 5,
    22: 10,
    23: 7,
    24: 5,
    25: 4,
    26: 1,
    27: 5,
    28: 12,
    29: 19,
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sb = p.supabase_client()
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
    unit_id = sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data[0]["id"]

    existing = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,name,catalog_slug,expected_question_count")
        .eq("unit_id", unit_id)
        .execute()
        .data
        or []
    )
    by_no = {int(r["chapter_no"]): r for r in existing}
    print("before", [(r["chapter_no"], r["name"], r["catalog_slug"]) for r in existing], flush=True)

    # Free 17–19: bump the live calculus rows out of the way first.
    for old in (21, 20, 19):
        row = by_no.get(old)
        if not row:
            continue
        tmp = old + 1000
        sb.table("pyq_chapters").update({"chapter_no": tmp}).eq("id", row["id"]).execute()
        print(f"  bump {old} -> {tmp} id={row['id']} {row['name']}", flush=True)

    existing = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,name,catalog_slug,expected_question_count")
        .eq("unit_id", unit_id)
        .execute()
        .data
        or []
    )
    by_slug = {r["catalog_slug"]: r for r in existing}

    for no, name, slug in p.MATH_2025_SESSION_CHAPTERS:
        want_expected = JAN_2025_COUNTS[no]
        row = by_slug.get(slug)
        if row:
            patch = {"chapter_no": no, "name": name, "catalog_slug": slug}
            # Keep the multi-year DI expected count; fill only when unset.
            if row.get("expected_question_count") is None:
                patch["expected_question_count"] = want_expected
            sb.table("pyq_chapters").update(patch).eq("id", row["id"]).execute()
            print(f"  update id={row['id']} -> ch{no} {name}", flush=True)
            continue
        rec = (
            sb.table("pyq_chapters")
            .insert({
                "unit_id": unit_id,
                "chapter_no": no,
                "name": name,
                "catalog_slug": slug,
                "expected_question_count": want_expected,
            })
            .execute()
            .data
        )
        print(f"  insert id={rec[0]['id']} ch{no} {name}", flush=True)

    after = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,name,catalog_slug")
        .eq("unit_id", unit_id)
        .order("chapter_no")
        .execute()
        .data
        or []
    )
    print("after", [(r["chapter_no"], r["id"], r["name"]) for r in after], flush=True)
    if [r["chapter_no"] for r in after] != list(range(1, 30)):
        raise SystemExit("expected chapter_no 1..29 in order")
    if [r["catalog_slug"] for r in after] != [slug for _n, _t, slug in p.MATH_2025_SESSION_CHAPTERS]:
        raise SystemExit("catalog_slug mismatch vs 2025 session TOC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
