#!/usr/bin/env python3
"""Phase 2a - seed subject, unit, 32 chapters and their topics. No cost."""
import pyq_common as p


def main():
    sb = p.supabase_client()
    skeleton = p.load_skeleton()
    key = p.load_answer_key()

    subject = sb.table("pyq_subjects").upsert(
        {"name": "Physics"}, on_conflict="name").execute().data[0]

    unit = sb.table("pyq_units").upsert(
        {"subject_id": subject["id"],
         "name": "JEE Main Physics (MathonGo PYQ)",
         "sort_order": 1},
        on_conflict="subject_id,name").execute().data[0]

    # chapters: expected_question_count from the book's own answer key
    chapter_rows = []
    for chapter_no_str, entry in key.items():
        chapter_no = int(chapter_no_str)
        chapter_rows.append({
            "unit_id": unit["id"],
            "chapter_no": chapter_no,
            "name": entry["title"],
            "expected_question_count": len(entry["answers"]),
            "catalog_slug": p.CATALOG_SLUG[chapter_no],
        })
    chapter_rows.sort(key=lambda r: r["chapter_no"])
    sb.table("pyq_chapters").upsert(chapter_rows, on_conflict="chapter_no").execute()

    chapters = {c["chapter_no"]: c["id"] for c in
                sb.table("pyq_chapters").select("id,chapter_no").execute().data}

    # topics: verbatim PDF headings, sort_order by first appearance in the skeleton
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
        topic_rows.append({"chapter_id": chapters[chapter_no], "name": name,
                           "sort_order": order})
    sb.table("pyq_topics").upsert(topic_rows, on_conflict="chapter_id,name").execute()

    print(f"subjects : 1")
    print(f"units    : 1")
    print(f"chapters : {len(chapter_rows)}")
    print(f"topics   : {len(topic_rows)}")
    print(f"expected total : {sum(r['expected_question_count'] for r in chapter_rows)}")
    print(f"null catalog_slug : "
          f"{[r['chapter_no'] for r in chapter_rows if r['catalog_slug'] is None]}")


if __name__ == "__main__":
    main()
