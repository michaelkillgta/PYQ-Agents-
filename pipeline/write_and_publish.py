#!/usr/bin/env python3
"""Write pass1 OCR bodies into pyq_questions and publish whitelist-valid rows.

Single-observer path: Sarvam Document AI + deterministic split.
Confidence 0.5 (one pass). Gemini / v2 chat are not used.
"""
import json

import pyq_common as p

FIG_RE = __import__("re").compile(r"\[\[fig:([^\]]+)\]\]")
JUNK_OPTION = __import__("re").compile(
    r"^(√|N|\*)$"
)
OPTION_FOOTER = __import__("re").compile(
    r"\d{1,3}(?:\s+\d{1,3})+\s*mi\s*$", __import__("re").I
)


def options_publishable(options) -> bool:
    """Four printed answers. Blank / page-number / lone √ options are unanswerable."""
    if not options or len(options) != 4:
        return False
    for raw in options:
        t = (raw or "").strip()
        if not t or JUNK_OPTION.fullmatch(t) or OPTION_FOOTER.search(t):
            return False
    return True


def main():
    sb = p.supabase_client()
    parsed = json.loads(
        (p.OUT / "extracted" / "pass1" / "parsed.json").read_text(encoding="utf-8")
    )
    skeleton = {
        str(r["q_no"]): r
        for r in p.load_skeleton()
        if r["chapter_no"] == p.CHAPTER_5
    }

    ch5_id = sb.table("pyq_chapters").select("id").eq(
        "chapter_no", p.CHAPTER_5).execute().data[0]["id"]
    q_ids = {str(r["q_no"]): r["id"] for r in sb.table("pyq_questions")
             .select("id,q_no").eq("chapter_id", ch5_id).execute().data}

    option_rows = []
    publishable = []
    skipped = []
    for q_no, entry in parsed.items():
        spec = skeleton[q_no]
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

    print(f"parsed       : {len(parsed)}")
    print(f"published    : {len(publishable)}")
    print(f"held back    : {len(skipped)}")
    print(f"options wrote: {len(option_rows)}")
    if skipped:
        print("held:", sorted(skipped, key=lambda x: x["q_no"]))


if __name__ == "__main__":
    main()
