#!/usr/bin/env python3
"""Read-only verification of the Phase 1 outputs. Writes analysis.json."""
import json
from collections import Counter
from pathlib import Path

OUT = Path("./out")

skeleton = json.loads((OUT / "skeleton.json").read_text())
figures = json.loads((OUT / "figures.json").read_text())
answer_key = json.loads((OUT / "answer_key.json").read_text())
orphans = json.loads((OUT / "orphan_figures.json").read_text())

report = {
    "totals": {
        "skeleton_questions": len(skeleton),
        "figures": len(figures),
        "answer_key_answers": sum(len(c["answers"]) for c in answer_key.values()),
        "answer_key_chapters": len(answer_key),
        "orphan_figures": len(orphans),
        "null_exam_date_total": sum(1 for r in skeleton if not r["exam_date"]),
        "null_topic": sum(1 for r in skeleton if not r["topic"]),
        "null_tier": sum(1 for r in skeleton if not r["tier"]),
        "with_figure": sum(1 for r in skeleton if r["figure_keys"]),
        "figure_links": sum(len(r["figure_keys"]) for r in skeleton),
        "out_of_syllabus": sum(1 for r in skeleton if r["out_of_syllabus"]),
        "good_to_solve": sum(1 for r in skeleton if r["good_to_solve"]),
        "answer_type_counts": dict(Counter(r["answer_type"] for r in skeleton)),
    }
}

per_chapter = []
counts = Counter(r["chapter_no"] for r in skeleton)
for cno in sorted(answer_key, key=lambda k: int(k)):
    c = answer_key[cno]
    n = int(cno)
    per_chapter.append({
        "chapter_no": n,
        "title": c["title"],
        "expected": len(c["answers"]),
        "got": counts.get(n, 0),
        "pages": sorted({r["page"] for r in skeleton if r["chapter_no"] == n}),
    })
report["per_chapter"] = [
    {k: v for k, v in row.items() if k != "pages"} | {
        "page_range": f"{row['pages'][0]}-{row['pages'][-1]}" if row["pages"] else "-"
    }
    for row in per_chapter
]

# --- chapter 5 deep dive ---
c5 = [r for r in skeleton if r["chapter_no"] == 5]
report["chapter_5"] = {
    "title": answer_key.get("5", {}).get("title"),
    "count": len(c5),
    "expected": len(answer_key.get("5", {}).get("answers", {})),
    "answer_type": dict(Counter(r["answer_type"] for r in c5)),
    "with_figure": sum(1 for r in c5 if r["figure_keys"]),
    "figure_links": sum(len(r["figure_keys"]) for r in c5),
    "tier": dict(Counter(r["tier"] for r in c5)),
    "topics": sorted({r["topic"] for r in c5 if r["topic"]}),
    "topic_counts": dict(Counter(r["topic"] for r in c5)),
    "null_exam_date": sum(1 for r in c5 if not r["exam_date"]),
    "out_of_syllabus": sum(1 for r in c5 if r["out_of_syllabus"]),
    "good_to_solve": sum(1 for r in c5 if r["good_to_solve"]),
    "page_range": f"{min(r['page'] for r in c5)}-{max(r['page'] for r in c5)}" if c5 else "-",
    "exam_shift": dict(Counter(r["exam_shift"] for r in c5)),
}

# sample: first chapter-5 record that has a figure, else the first one
sample = next((r for r in c5 if r["figure_keys"]), c5[0] if c5 else None)
report["chapter_5_sample"] = sample

# figure key integrity
fig_keys = {f["figure_key"] for f in figures}
linked = {k for r in skeleton for k in r["figure_keys"]}
report["figure_integrity"] = {
    "manifest_keys": len(fig_keys),
    "linked_keys": len(linked),
    "linked_not_in_manifest": sorted(linked - fig_keys)[:20],
    "linked_not_in_manifest_count": len(linked - fig_keys),
    "unlinked_manifest_keys": len(fig_keys - linked),
    "orphan_file_keys": len({o["figure_key"] for o in orphans}),
}

# null-date distribution by chapter
report["null_date_by_chapter"] = dict(
    sorted(Counter(r["chapter_no"] for r in skeleton if not r["exam_date"]).items())
)

(OUT / "analysis.json").write_text(json.dumps(report, indent=2))

print(json.dumps({k: v for k, v in report.items() if k != "chapter_5_sample"}, indent=2))
print("--- SAMPLE ---")
print(json.dumps(report["chapter_5_sample"], indent=2))
