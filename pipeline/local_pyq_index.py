#!/usr/bin/env python3
"""Local PYQ index. Inventory never greps the repo or waits on Sarvam.

    python local_pyq_index.py --book math              # rebuild from skeleton + key
    python local_pyq_index.py --book math --held 2     # print held q_nos for PDF ch.2
    python local_pyq_index.py --book math --pull-db    # overlay review_status from TestBee

Root files: out-math/skeleton.json, out-math/answer_key.json, out-math/ocr/page_NNN.json
Index:      out-math/local.sqlite
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKS = {
    "math": ROOT / "out-math",
    "physics": ROOT / "out",
}

SLUG = {
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

DDL = """
CREATE TABLE IF NOT EXISTS questions (
  chapter_no INTEGER NOT NULL,
  q_no INTEGER NOT NULL,
  page INTEGER,
  slug TEXT,
  answer_type TEXT,
  pdf_key TEXT,
  review_status TEXT,
  ocr_json TEXT,
  PRIMARY KEY (chapter_no, q_no)
);
CREATE INDEX IF NOT EXISTS idx_q_status ON questions(slug, review_status);
"""


def connect(book: str) -> sqlite3.Connection:
    folder = BOOKS[book]
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder / "local.sqlite")
    db.row_factory = sqlite3.Row
    db.executescript(DDL)
    return db


def rebuild(book: str) -> int:
    folder = BOOKS[book]
    skeleton = json.loads((folder / "skeleton.json").read_text(encoding="utf-8"))
    keys = json.loads((folder / "answer_key.json").read_text(encoding="utf-8"))
    db = connect(book)
    db.execute("DELETE FROM questions")
    rows = []
    for r in skeleton:
        ch = int(r["chapter_no"])
        qn = int(r["q_no"])
        ans = (keys.get(str(ch)) or {}).get("answers", {}).get(str(qn)) or {}
        rows.append((
            ch,
            qn,
            r.get("page"),
            SLUG.get(ch) if book == "math" else r.get("catalog_slug"),
            ans.get("type") or r.get("answer_type"),
            str(ans.get("value") or r.get("answer_value") or ""),
            r.get("review_status"),
            str((folder / "ocr" / f"page_{int(r['page']):03d}.json").exists()),
        ))
    db.executemany(
        "INSERT INTO questions(chapter_no,q_no,page,slug,answer_type,pdf_key,review_status,ocr_json) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    db.commit()
    n = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    db.close()
    print(f"rebuilt {book} {n} rows -> {folder / 'local.sqlite'}")
    return 0


def held(book: str, chapter: int) -> int:
    db = connect(book)
    rows = db.execute(
        "SELECT q_no, page, pdf_key, review_status, ocr_json FROM questions "
        "WHERE chapter_no=? AND IFNULL(review_status,'unreviewed') NOT IN ('auto_ok','human_ok') "
        "ORDER BY q_no",
        (chapter,),
    ).fetchall()
    if not rows:
        # status never pulled — list all q_nos for the chapter
        rows = db.execute(
            "SELECT q_no, page, pdf_key, review_status, ocr_json FROM questions "
            "WHERE chapter_no=? ORDER BY q_no",
            (chapter,),
        ).fetchall()
        print(f"no review_status in local index; {len(rows)} skeleton rows for ch.{chapter}")
    else:
        print(f"held {len(rows)} ch.{chapter}")
    for r in rows:
        print(f"Q{r['q_no']}\tpage {r['page']}\tpdf {r['pdf_key']}\t{r['review_status']}\tocr={r['ocr_json']}")
    db.close()
    return 0


def pull_db(book: str) -> int:
    sys.path.insert(0, str(ROOT))
    import pyq_common as p

    p.configure_book(book)
    sb = p.supabase_client()
    unit = 3 if book == "math" else 1
    chapters = (
        sb.table("pyq_chapters").select("id,chapter_no,catalog_slug").eq("unit_id", unit).execute().data
        or []
    )
    id_to_ch = {c["id"]: int(c["chapter_no"]) for c in chapters}
    rows = []
    start = 0
    while True:
        batch = (
            sb.table("pyq_questions")
            .select("chapter_id,q_no,review_status")
            .in_("chapter_id", list(id_to_ch))
            .range(start, start + 999)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < 1000:
            break
        start += 1000
    db = connect(book)
    n = 0
    for q in rows:
        ch = id_to_ch.get(q["chapter_id"])
        if ch is None:
            continue
        db.execute(
            "UPDATE questions SET review_status=? WHERE chapter_no=? AND q_no=?",
            (q.get("review_status"), ch, int(q["q_no"])),
        )
        n += 1
    db.commit()
    db.close()
    print(f"pulled review_status for {n} rows")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=("math", "physics"), default="math")
    ap.add_argument("--held", type=int, metavar="CHAPTER")
    ap.add_argument("--pull-db", action="store_true")
    args = ap.parse_args()
    rebuild(args.book)
    if args.pull_db:
        pull_db(args.book)
    if args.held is not None:
        held(args.book, args.held)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
