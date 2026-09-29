#!/usr/bin/env python3
"""Phase 2 - insert all 4,115 skeleton rows (body = null, skeleton_only)
plus figure links for the pilot chapter. Idempotent on (chapter_id, q_no)."""
import pyq_common as p

BATCH = 500


def main():
    sb = p.supabase_client()
    skeleton = p.load_skeleton()

    chapters = {c["chapter_no"]: c["id"] for c in
                sb.table("pyq_chapters").select("id,chapter_no").execute().data}
    topics = {(t["chapter_id"], t["name"]): t["id"] for t in
              sb.table("pyq_topics").select("id,chapter_id,name").execute().data}

    rows = []
    for rec in skeleton:
        chapter_id = chapters[rec["chapter_no"]]
        mcq = rec["answer_type"] == "mcq"
        rows.append({
            "chapter_id": chapter_id,
            "topic_id": topics.get((chapter_id, rec["topic"])),
            "q_no": rec["q_no"],
            "tier": rec["tier"],
            # D8: format is derived from the answer key only. Models never set it.
            "format": "mcq" if mcq else "numerical",
            "body": None,
            "correct_option": int(rec["answer_value"]) if mcq else None,
            "numerical_answer": None if mcq else rec["answer_value"],
            "exam_date": rec["exam_date"],
            "exam_shift": rec["exam_shift"],
            "out_of_syllabus": rec["out_of_syllabus"],
            "good_to_solve": rec["good_to_solve"],
            "source_page": rec["page"],
            "source_bbox": rec["bbox"],
            "review_status": "skeleton_only",
        })

    for i in range(0, len(rows), BATCH):
        sb.table("pyq_questions").upsert(
            rows[i:i + BATCH], on_conflict="chapter_id,q_no").execute()
    print(f"questions upserted : {len(rows)}")

    # figure links for the pilot chapter
    ch5_id = chapters[p.CHAPTER_5]
    q_ids = {q["q_no"]: q["id"] for q in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch5_id).execute().data}
    fig_ids = {f["figure_key"]: f["id"] for f in
               sb.table("pyq_figures").select("id,figure_key").execute().data}

    links = []
    for rec in skeleton:
        if rec["chapter_no"] != p.CHAPTER_5:
            continue
        for order, key in enumerate(rec["figure_keys"]):
            links.append({"figure_id": fig_ids[key],
                          "question_id": q_ids[rec["q_no"]],
                          "option_id": None,
                          "role": "question_body",
                          "sort_order": order})

    existing = {(l["figure_id"], l["question_id"]) for l in sb.table("pyq_figure_links")
                .select("figure_id,question_id").execute().data}
    fresh = [l for l in links
             if (l["figure_id"], l["question_id"]) not in existing]
    if fresh:
        sb.table("pyq_figure_links").insert(fresh).execute()
    print(f"figure links total : {len(links)}  inserted now: {len(fresh)}")


if __name__ == "__main__":
    main()
