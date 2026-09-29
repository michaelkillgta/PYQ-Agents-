# PYQ Ingestion Pipeline — Build Plan

Agent instructions for building the JEE Main Physics question-bank ingestion
pipeline. Work phase by phase. Do not skip ahead. Each phase has an acceptance
gate that must pass before the next phase starts.

---

## Context

Source: `MathonGo_PYQ_Book__JEE_Main_2025_-_2019__-_Physics.pdf`
463 pages · 32 chapters · 4,115 questions · 1,337 figures · digital-born (not scanned)

Target: Supabase Postgres + Supabase Storage.

The PDF has a full text layer with glyph coordinates. Figures are embedded raster
objects with known bounding boxes. There are **no vector-drawn diagrams** (verified).
The answer key on pages 455–463 is plain text and gives ground truth for question
counts and answers.

---

## Invariants — never violate these

1. **The skeleton is immutable.** After Phase 1, `skeleton.json` defines every
   question that exists. No later stage may add, remove, renumber, or re-link a
   question. Models may only fill `body` and `options`.

2. **Whitelist enforcement at the parser.** If a model returns a `q_no` not in the
   skeleton, or a `figure_key` not on that page's list, reject the response and
   retry that page. Never write unknown keys to the database.

3. **Never use a layout-detection model** (Docling, Surya, LayoutParser) on this
   PDF. Coordinates are available; prediction is strictly worse. This rule applies
   only to digital-born PDFs — check `page.get_text("dict")` returns spans first.

4. **Never base64 an image into a Postgres column.** Store the storage path.

5. **Retries must escalate to a different model.** Re-running the same model on a
   failed page reproduces systematic misreads. Retry ≠ verification.

6. **Do not claim an accuracy number that was not measured** against the Phase 8
   gold sample.

---

## Environment

```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SARVAM_API_KEY=
GEMINI_API_KEY=        # fallback observer only
```

Python deps: `pymupdf`, `supabase`, `httpx`, `pydantic`, `tenacity`.

Working layout:
```
./out/
  figures/            1,337 PNGs
  pages/              454 page rasters @200dpi
  figures.json        figure manifest with bboxes
  answer_key.json     32 chapters, 4,115 answers
  skeleton.json       THE SPINE — 4,115 records
  orphan_figures.json 88 unassigned
  extracted/          Phase 5+6 model output
  review_queue.json   Phase 9 output
```

---

## Phase 1 — Skeleton — DONE

Scripts `extract_assets.py` and `build_skeleton.py` already exist and pass.

```bash
python extract_assets.py book.pdf ./out
python build_skeleton.py book.pdf ./out
```

Verified output: 4,115 questions · 32/32 chapters reconcile · tier 100% ·
topic 100% · answers 100% · dates 94.5% · 947 questions with figures · 88 orphans.

**Gate:** `chapters mismatching = 0`. If not zero, stop and report — do not proceed.

---

## Phase 2 — Storage

Task:
1. Apply `schema.sql` to Supabase.
2. Populate `chapters.expected_question_count` from `answer_key.json`.
3. Deduplicate figures by SHA-256 (1,337 files → 1,325 unique; the 10 duplicate
   pairs are page-spanning questions — keep one file, link twice).
4. Upload to Supabase Storage bucket `pyq/physics/figures/`, object name =
   `figure_key`. Idempotent: re-running must overwrite, not duplicate.
5. Insert all 4,115 skeleton rows with `body = null`,
   `review_status = 'skeleton_only'`.

**Gate:** `select * from v_ingestion_check` returns `delta = 0` on all 32 rows,
and `select count(*) from figures` = 1,325.

---

## Phase 3 — Resolve orphans and missing dates

88 orphan figures and 228 questions without an exam date. Both are the same
page-boundary artifact. No AI.

Rule to implement: an orphan sitting at the top of a column (y < 60) belongs to
the last question of that same column on the previous page. The 10 duplicate-
checksum pairs confirm which questions span pages.

For the 228 undated questions: the date tag is on the continuation page. Search
the top of the next page's matching column.

**Gate:** orphan figures < 15, undated questions < 40. Remaining ones get a
manual pass — emit `manual_review.json` listing them with page numbers.

---

## Phase 4 — Bake-off (decision gate, do not skip)

Select 20 pages: easy (p21, no figures), hard (p8, match-list with 4 option
images), dense math (a Rotational Motion page with integrals), plus 17 random.

Run three candidates on those pages:
- `gemma4` via Sarvam `/v2/chat/completions` (image input)
- Sarvam Vision via the Doc Agents dashboard (manual, ~15 min)
- `gemini-flash-lite` (external control)

Score automatically against the skeleton: question count, q_no set, figure_key
placement. Score LaTeX correctness by human eye on those 20 pages only.

Write `bakeoff_results.md` with a table and a recommendation.

**Gate:** leader ≥ 90% LaTeX correctness → proceed with that model.
If nothing clears 80%, STOP and report. Do not spend the extraction budget.

---

## Phase 5 — Constrained extraction

For each of 454 pages, build a prompt containing that page's skeleton slice:
question numbers in reading order, which question owns which figure keys, tier,
topic, exam dates. Instruct the model that its only job is:

- transcribe the question stem as Markdown with inline LaTeX (`$...$`)
- split the four options (or mark numerical)
- place `[[fig:KEY]]` placeholders using only the supplied keys

Set `temperature = 0`, `response_format = json`. Concurrency 8, respect
Sarvam's 60 req/min on Starter. Persist raw responses to `./out/extracted/pass1/`
so a crash never costs a re-run.

**Gate:** every page returns valid JSON whose q_no set exactly matches the
skeleton for that page. Estimated cost ₹127.

---

## Phase 6 — Second observer

Repeat Phase 5 with a **different** model into `./out/extracted/pass2/`.

Normalise LaTeX before diffing (collapse whitespace, `\dfrac`→`\frac`,
`\left(`→`(`) so cosmetic differences don't create false flags.

Emit `diff_report.json`: per question, `agree | differ`, with both variants.
Expect 10–15% disagreement.

**Gate:** diff report covers all 4,115. Estimated cost ₹127.

---

## Phase 7 — Solve-verify

For each question send to a reasoning model (`glm5.3-flash` on Sarvam):
the extracted LaTeX stem, the options, **and the figure images** for the 947
questions that have them. Ask only for the answer — option number or numeric value.

Compare to `answer_value` from the skeleton. Record `solve_match: true|false`.

Known blind spot, document it in the output: this validates the answer path only.
It cannot detect corruption in the 9,882 distractor strings, or in stem details
that don't affect the calculation.

**Gate:** all 4,115 have a verdict. Estimated cost ~₹500.

---

## Phase 8 — Gold sample

Randomly sample 200 questions, stratified by chapter, figure/no-figure, and
MCQ/numerical. Emit `gold_sample.html` — a simple review page showing the page
crop beside the extracted body, options, figures, and answer.

A human verifies every character. Their corrections are recorded.

Compute the true error rate with a 95% confidence interval, separately for
answer-affecting content and distractor content. Write `accuracy_report.md`.

**Gate:** this number is the only accuracy figure anyone is allowed to quote.

---

## Phase 9 — Review queue

Build `review_queue.json` from: two-model disagreement, `solve_match = false`,
or low model confidence.

Rank riskiest first — questions with figures, then match-lists, then by LaTeX
token density. Expect 300–1,200 items.

Ship a minimal review UI: page crop on the left, editable extraction on the
right, approve/fix buttons. On approve set `review_status = 'human_ok'`.

**Gate:** queue empty or consciously deferred. Publish only rows where
`review_status in ('auto_ok','human_ok')`.

---

## Budget

| Phase | Cost |
|---|---|
| 1–3 | ₹0 |
| 4 bake-off | ~₹50 |
| 5 extraction | ~₹127 |
| 6 second observer | ~₹127 |
| 7 solve-verify | ~₹500 |
| **Total** | **~₹800 of ₹30,000 Sarvam credits** |

Real money spend: ₹0.

---

## Reporting

After each phase append to `PROGRESS.md`: phase, gate result, actual numbers,
actual cost, anything that surprised you. If a gate fails, stop and write up why
rather than working around it.
