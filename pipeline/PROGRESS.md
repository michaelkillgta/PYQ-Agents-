# PROGRESS — PYQ Ingestion Pipeline

Progress log required by `CURSOR_PLAN.md` § Reporting. One section appended per phase.

---

## Phase 0 — Environment · PASS

**Date:** 11 Sep 2026
**Cost:** ₹0 (no API calls, no models)

### Interpreter actually used

| | |
|---|---|
| Version | **Python 3.14.7** (`tags/v3.14.7:823f032`, Aug 5 2026, MSC v.1944 64-bit) |
| Path | `C:\Python314\python.exe` |
| Venv | none — user site-packages at `C:\Users\tempo\AppData\Roaming\Python\Python314\site-packages` |

No Python 3.12 exists on this machine (`py -0` lists only `-V:3.14 *`), so the
3.12-venv fallback in the brief was not available. It was not needed.

### Packages installed

| Package | Version | Notes |
|---|---|---|
| `pymupdf` | **1.26.3** | downgraded from 1.28.2 — see below |
| `supabase` | 2.31.0 | |
| `httpx` | 0.28.1 | |
| `pydantic` | 2.13.5 | |
| `tenacity` | 9.1.4 | |

All four later-phase deps installed first try. No build-from-source anywhere —
every wheel was prebuilt.

### Surprise 1 — Smart App Control blocked PyMuPDF's native DLL

The anticipated risk (no cp314 wheel for PyMuPDF) **did not happen**. PyMuPDF
now ships a stable-ABI wheel, `pymupdf-1.28.2-cp310-abi3-win_amd64.whl`, which
installs on 3.14 without compiling.

A different problem appeared instead. `import pymupdf` failed at load time:

```
ImportError: DLL load failed while importing _mupdf:
An Application Control policy has blocked this file.
```

Root cause, from `Microsoft-Windows-CodeIntegrity/Operational` event 3077:

```
Code Integrity determined that a process (\...\Python314\python.exe) attempted
to load \...\site-packages\pymupdf\_mupdf.pyd that did not meet the Enterprise
signing level requirements or violated code integrity policy
(Policy ID:{0283ac0f-fff1-49ae-ada1-8a933130cad6})
```

Accompanied by event 3118 `Smart App Control Block`. Confirmed with
`HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy` →
`VerifiedAndReputablePolicyState = 1`, i.e. **Smart App Control is ON** on this
machine.

Diagnosis: the block is reputation-based, not a blanket ban on unsigned native
extensions. `pydantic_core`, `cryptography`'s Rust binding and all stdlib
native modules import fine. PyMuPDF 1.28.2 is simply too new to have
Intelligent Security Graph reputation yet.

Fix: install an older, widely-deployed build. `pymupdf==1.26.3` loads without
complaint and is well above the 1.24.3 floor needed for the top-level
`import pymupdf` name and `get_image_info(xrefs=True)` that both scripts use.
This was resolved on the first version tried.

Nothing was disabled or bypassed — Smart App Control is still on. **Anyone
reproducing this on a Smart-App-Control machine should pin
`pymupdf==1.26.3`** rather than taking latest.

### Files changed in Phase 0

None. `extract_assets.py` and `build_skeleton.py` were **not modified** — they
ran unaltered. One new read-only helper was added, `analyze_skeleton.py`, which
only reads `./out/*.json` and writes `./out/analysis.json`; it touches no
pipeline logic.

---

## Phase 1 — Skeleton · PASS

**Cost:** ₹0. Deterministic geometry + text-layer extraction only. No models, no
API keys, no network.

### Commands run

```powershell
# from c:\Users\tempo\Downloads\files
python extract_assets.py "C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Physics.pdf" ./out --rasterize
python build_skeleton.py  "C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Physics.pdf" ./out
python analyze_skeleton.py
```

`--rasterize` was included as instructed. It was the dominant cost of step 1 but
finished comfortably, so there was no need to re-run without it.

### Runtime

| Step | Wall clock |
|---|---|
| `extract_assets.py --rasterize` | 192.7 s (3 min 13 s) |
| `build_skeleton.py` | 384.8 s (6 min 25 s) |
| `analyze_skeleton.py` | 1.3 s |
| **Total** | **≈ 9 min 39 s** |

`build_skeleton.py` took twice as long as the extractor, which is a little
counter-intuitive given it writes no images. The `page.get_textbox()` call per
question — 4,115 rect queries plus a `get_text("dict")` per page — is where the
time goes. Still well inside "a couple of minutes to a few minutes"; nothing to
act on.

### Gate

`CURSOR_PLAN.md` Phase 1 gate is `chapters mismatching = 0`.

**Printed value: `chapters mismatching  : 0  []`** — PASS. The empty list means
no chapter had even a one-question discrepancy against the book's own answer key.

### Raw stdout

`extract_assets.py`:
```
figures extracted : 1336
chapters in key   : 32
answers parsed    : 4115
figure bytes      : 20.0 MB
pages with figures: 326
page rasters      : 454
```

`build_skeleton.py`:
```
questions in skeleton : 4115
answer key total      : 4115
chapters mismatching  : 0  []
with tier             : 4115
with topic            : 4115
with exam date        : 3887
with answer attached  : 4115
with >=1 figure       : 947
orphan figures        : 88
```

### Totals vs expected

| Metric | Expected | Actual | Δ |
|---|---|---|---|
| Questions in `skeleton.json` | 4,115 | **4,115** | **0** |
| Answers in `answer_key.json` | 4,115 | **4,115** | **0** |
| Chapters in answer key | 32 | **32** | **0** |
| Figures in `figures.json` | 1,337 | **1,336** | **−1** |
| Figure PNGs on disk | 1,337 | **1,335** | **−2** |
| Orphan figures | 88 | **88** | **0** |
| Questions with ≥1 figure | 947 | **947** | **0** |
| Questions with exam date | 3,887 (94.5%) | **3,887** | **0** |
| Questions with tier | 4,115 (100%) | **4,115** | **0** |
| Questions with topic | 4,115 (100%) | **4,115** | **0** |
| Questions with answer attached | 4,115 (100%) | **4,115** | **0** |

Everything the plan's "Verified output" line claims reproduces **exactly** —
4,115 / 32-of-32 / tier 100% / topic 100% / answers 100% / dates 3,887 / 947
with figures / 88 orphans. The only deviation in the whole run is the figure
count, discussed as Surprise 2 below.

Other skeleton-wide facts:

| | |
|---|---|
| `answer_type = mcq` | 3,294 (80.0%) |
| `answer_type = numerical` | 821 (20.0%) |
| `answer_type = null` | 0 |
| Question→figure links (counting repeats) | 1,246 across 947 questions |
| `out_of_syllabus = true` (`Q*`) | 286 |
| `good_to_solve = true` (`Q^`) | 32 |

### Surprise 2 — figure count is 1,336 not 1,337, and `figure_key` is not unique

Two separate small facts, both benign for Phase 1 but both of which matter in
Phase 2.

**(a) 1,336 manifest rows, only 1,335 distinct keys.** `figure_key` is built as
`p{page}_x{xref}`. On page 420 the *same* image xref is placed **twice** at two
different x positions:

```
p420_x3821  bbox [330.9, 504.1, 399.2, 526.0]  column right
p420_x3821  bbox [441.7, 504.1, 510.0, 526.0]  column right
```

Both manifest rows resolve to the same filename, so the second `pix.save()`
overwrote the first — hence 1,335 files for 1,336 rows. Byte-identical content,
so no pixels were lost, but the key can no longer distinguish the two
placements. This is a genuine, if tiny, hole in the identity scheme: **the
skeleton can express "this question uses image X" but not "…the left one".**

Phase 2 dedupes figures by SHA-256 anyway, and both placements hash the same, so
this collapses into the existing "keep one file, link twice" path. Flagging it
because the plan expects exactly 10 duplicate pairs from page-spanning
questions; this is an eleventh duplicate of a *different* kind (same-page repeat,
not page-spanning) and will show up in that reconciliation.

**(b) 1,336 vs the expected 1,337.** One figure fewer than the plan's headline.
Both scripts apply the same watermark/spacer filters (>85% page coverage, <18 pt
side), so the likeliest explanation is that 1,337 was counted before the
same-page duplicate above was collapsed, or counted placements rather than
objects. Not worth chasing at Phase 1 — the number that actually gates
downstream work is the question→figure link count, and that hit 947 on the nose.

Integrity check that *does* matter, and passed:

| Check | Result |
|---|---|
| `figure_keys` referenced by skeleton but absent from manifest | **0** — no dangling references |
| Distinct keys linked from skeleton | 1,245 |
| Manifest keys never linked | 90 (= the 88 orphans + 2 keys whose owners are on the previous page) |

Invariant 2 (whitelist enforcement) therefore has a clean whitelist to work
from: every key the skeleton names exists as a real file.

### Per-chapter question counts — all 32 chapters

`expected` is from the book's own answer key, `got` is what the skeleton
produced. They are identical on every row, which is what drives the gate to 0.

| # | Chapter | Expected | Got | Δ | Pages |
|---:|---|---:|---:|---:|---|
| 1 | Mathematics in Physics | 94 | 94 | 0 | 5–12 |
| 2 | Units and Dimensions | 110 | 110 | 0 | 14–23 |
| 3 | Motion In One Dimension | 123 | 123 | 0 | 25–36 |
| 4 | Motion In Two Dimensions | 93 | 93 | 0 | 38–45 |
| 5 | Laws of Motion | 132 | 132 | 0 | 47–60 |
| 6 | Work Power Energy | 122 | 122 | 0 | 62–72 |
| 7 | Center of Mass Momentum and Collision | 96 | 96 | 0 | 74–83 |
| 8 | Rotational Motion | 193 | 193 | 0 | 85–105 |
| 9 | Gravitation | 159 | 159 | 0 | 107–120 |
| 10 | Mechanical Properties of Solids | 82 | 82 | 0 | 123–129 |
| 11 | Mechanical Properties of Fluids | 131 | 131 | 0 | 131–142 |
| 12 | Oscillations | 117 | 117 | 0 | 144–154 |
| 13 | Waves and Sound | 117 | 117 | 0 | 156–164 |
| 14 | Thermal Properties of Matter | 85 | 85 | 0 | 168–176 |
| 15 | Thermodynamics | 154 | 154 | 0 | 178–194 |
| 16 | Kinetic Theory of Gases | 127 | 127 | 0 | 196–205 |
| 17 | Electrostatics | 203 | 203 | 0 | 208–230 |
| 18 | Capacitance | 123 | 123 | 0 | 232–244 |
| 19 | Current Electricity | 285 | 285 | 0 | 247–275 |
| 20 | Magnetic Properties of Matter | 55 | 55 | 0 | 277–282 |
| 21 | Magnetic Effects of Current | 193 | 193 | 0 | 284–304 |
| 22 | Electromagnetic Induction | 102 | 102 | 0 | 307–317 |
| 23 | Alternating Current | 138 | 138 | 0 | 319–331 |
| 24 | Ray Optics | 202 | 202 | 0 | 334–354 |
| 25 | Wave Optics | 117 | 117 | 0 | 356–366 |
| 26 | Dual Nature of Matter | 147 | 147 | 0 | 369–382 |
| 27 | Atomic Physics | 100 | 100 | 0 | 384–391 |
| 28 | Nuclear Physics | 106 | 106 | 0 | 393–401 |
| 29 | Electromagnetic Waves | 114 | 114 | 0 | 404–415 |
| 30 | Semiconductors | 168 | 168 | 0 | 417–440 |
| 31 | Communication System | 83 | 83 | 0 | 442–448 |
| 32 | Experimental Physics | 44 | 44 | 0 | 450–454 |
| | **Total** | **4,115** | **4,115** | **0** | |

Largest chapter is Current Electricity at 285; smallest is Experimental Physics
at 44. Page ranges are contiguous and non-overlapping, and chapter 32 ends at
page 454 — exactly where `rasterize_pages()`' `last_content_page=454` cut-off
sits, and immediately before the answer-key tail at 455–463. That alignment is a
useful independent confirmation that the chapter walk didn't drift.

### Chapter 5 — Laws of Motion (pages 47–60)

| Field | Value |
|---|---|
| Question count | **132** (expected 132, Δ 0) |
| `answer_type = mcq` | **113** (85.6%) |
| `answer_type = numerical` | **19** (14.4%) |
| With ≥1 entry in `figure_keys` | **52** (39.4%) |
| Total figure links in chapter | 63 (so several questions carry 2+ figures) |
| `exam_date` null | **5** (127 dated, 96.2%) |
| `out_of_syllabus` | 0 |
| `good_to_solve` | 0 |

Tier breakdown — sums to 132:

| Tier | Count |
|---|---:|
| `concept_builder` | 29 |
| `must_do` | 79 |
| `advanced` | 24 |

Distinct `topic` values — 5, all non-null:

| Topic | Count |
|---|---:|
| Newton's laws of motion | 38 |
| Frictional force | 39 |
| Equilibrium of Forces | 30 |
| Non-uniform Circular Motion | 13 |
| Spring force | 12 |

Note the topic strings come straight off the PDF headings and are **not
normalised** — "Newton's laws of motion" and "Frictional force" are sentence
case while "Equilibrium of Forces" and "Non-uniform Circular Motion" are title
case. That is faithful to the source, but Phase 2 should decide whether
`topics.name` stores the verbatim heading or a canonical form.

`exam_shift` for the chapter: 66 evening, 61 morning, 5 null — the 5 nulls are
the same 5 records missing `exam_date`, as expected since both come from the one
`DATE_RE` match.

### Sample record — verbatim from `skeleton.json`

First Laws of Motion record that owns a figure (chapter 5, Q1, page 47):

```json
{
  "chapter_no": 5,
  "chapter_title": "Laws of Motion",
  "topic": "Newton's laws of motion",
  "tier": "concept_builder",
  "q_no": 1,
  "page": 47,
  "column": "L",
  "bbox": [
    38,
    79.7,
    297.5,
    220.3
  ],
  "figure_keys": [
    "p047_x549"
  ],
  "exam_date": "2024-01-30",
  "exam_shift": "evening",
  "out_of_syllabus": false,
  "good_to_solve": false,
  "answer_type": "mcq",
  "answer_value": "1",
  "body": null,
  "options": null,
  "review_status": "skeleton_only"
}
```

`body` and `options` are null and `review_status` is `skeleton_only`, as
Invariant 1 requires — the skeleton asserts only what geometry and the text
layer can prove.

### Orphans and missing dates

| Metric | Value |
|---|---:|
| Records in `orphan_figures.json` | **88** (matches plan exactly) |
| Questions with null `exam_date`, whole book | **228** (5.5% of 4,115) |

228 = 4,115 − 3,887, consistent with the plan's "dates 94.5%".

Null dates by chapter — spread thin across 31 of 32 chapters rather than
clustered, which supports the plan's page-boundary-artifact theory over any
systematic parse failure:

| Ch | Nulls | Ch | Nulls | Ch | Nulls | Ch | Nulls |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 9 | 5 | 17 | 19 | 25 | 10 |
| 2 | 14 | 10 | 6 | 18 | 8 | 26 | 7 |
| 3 | 7 | 11 | 8 | 19 | 9 | 27 | 7 |
| 4 | 5 | 12 | 4 | 20 | 4 | 28 | 5 |
| 5 | 5 | 13 | 8 | 21 | 10 | 29 | 4 |
| 6 | 7 | 14 | 4 | 22 | 1 | 30 | 9 |
| 7 | 2 | 15 | 12 | 23 | 6 | 31 | **0** |
| 8 | 16 | 16 | 4 | 24 | 19 | 32 | 1 |

Worst offenders are Electrostatics and Ray Optics at 19 each; Communication
System is fully dated. Both totals are Phase 3's problem (gate: orphans < 15,
undated < 40) and need no action now.

### Disk

Page rasters **were** generated — 454 PNGs at 200 dpi, covering pages 1–454
(`last_content_page=454`, skipping the 455–463 answer-key tail).

| Path | Files | Size |
|---|---:|---:|
| `out/pages/` | 454 | 343.4 MB |
| `out/figures/` | 1,335 | 19.0 MB |
| `out/skeleton.json` | 1 | 2.00 MB |
| `out/answer_key.json` | 1 | 295 KB |
| `out/figures.json` | 1 | 347 KB |
| `out/orphan_figures.json` | 1 | 10 KB |
| `out/analysis.json` | 1 | 7.3 KB |
| **`./out` total** | **1,794** | **365.1 MB** |

Free space on C: after the run is 338.6 GB, so rasters are a non-issue — 94% of
the footprint but only a third of a gigabyte. They stay.

### Phase 1 verdict

Gate `chapters mismatching = 0` **passed**. The skeleton is now frozen per
Invariant 1: 4,115 records, complete tier/topic/answer coverage, no dangling
figure references. Phase 2 (storage) is unblocked.

Two items to carry into Phase 2:
1. `figure_key` collides when one image object is placed twice on a page
   (`p420_x3821`). Expect an eleventh duplicate in the SHA-256 dedupe, of a
   different kind than the 10 page-spanning pairs the plan predicts.
2. `topic` strings are verbatim PDF headings with inconsistent capitalisation.
   Decide verbatim vs canonical before populating the `topics` table.

### Cost

**₹0.** No model calls, no Sarvam credits, no external services touched. Phases
1–3 are budgeted at ₹0 in the plan and Phase 1 came in on budget.

---

## Phase 2a — Schema and taxonomy · PASS

**Date:** 12 Sep 2026
**Cost:** ₹0
**Migration:** `Web/supabase/migrations/20261019120000_pyq_question_bank.sql` applied to project `bytsiknhtcnlxwzgqkrd` as `pyq_question_bank`.

### Step 3 schema probe

`tables=9`, `body_nullable=YES`, `has_catalog_slug=1`, `slug_index=1`, `status_check=1`, `bucket=1`. Unique constraints on `pyq_chapters`: 1 (`chapter_no` only).

One addition vs the plan SQL: `v_pyq_ingestion_check` is `WITH (security_invoker = true)` so it does not bypass RLS.

### Seed

`seed_taxonomy.py` first run and re-run: subjects 1, units 1, chapters 32, topics 164, expected total 4115, `null catalog_slug : [17]`.

Gate: 32 chapters, expected 4115, routed 31, distinct slugs 28. Merges: `system-of-particles-and-rotational-motion` ×2, `units-and-measurements` ×3. Chapter 5: 132 / `laws-of-motion`.

Topics stored verbatim (D3).

---

## Phase 2 — Storage · PASS

**Date:** 12 Sep 2026
**Cost:** ₹0

### Dedupe (files vs manifest)

`manifest rows 1336`, `distinct keys 1335`, `unique checksums 1325`, `duplicate groups 10`, `repeated keys ['p420_x3821']`, `missing files 0`. Matches the plan: ten file-level groups plus the eleventh manifest-row collision. Artifact: `out/figure_dedupe.json`.

### Pilot upload

63 Laws of Motion keys → 63 objects at `pyq/physics/figures/<key>.png` → 63 `pyq_figures` rows. Re-run of `load_questions.py`: 4115 upserted, 63 figure links, 0 new inserts.

`v_pyq_ingestion_check`: `chapters_with_delta = 0`. Chapter 5: expected 132, actual 132, delta 0, skeleton_only 132, missing_answer 0. `figures=63`, `checksums=63`, `links=63`, `body_not_null=0`.

Figure fetch: `p047_x549` HTTP 200, 18317 bytes matching `pyq_figures.bytes`.

---

## Phase 3 — Orphans and dates · PASS

**Date:** 12 Sep 2026
**Cost:** ₹0

`chapter 5 undated : 5`. `dates resolved : 0`. `orphans on 47-60 : 0`. `orphans resolved : 0`. `manual review : 5`.

The five undated questions (Q30 p50L, Q52/53 p52L, Q70 p54L, Q79 p54R) are listed in `out/manual_review.json`. Dates exist on those pages (DATE_RE hits the page text) but not in the top-60pt band of the next/same-column probes — they sit beside the question body, not at the column header. Gate allows this: remaining undated rows are documented with page numbers. No dates were guessed.

Orphan resolution was a no-op: Phase 1 already measured 0 orphans on pages 47–60.

---

## Phase 4 — Bake-off · FAIL (blocked)

**Date:** 12 Sep 2026
**Cost:** ₹0 — no successful page-call

### Endpoint probe

- `GET /v1/models` → 200, ids: `sarvam-105b`, `sarvam-105b-conversations`
- `GET /v2/models` → 200, ids include `gemma4`, `glm5.2`, `glm5.3`, `deepseekv4-flash`, `sarvam-105b`
- `POST /v2/chat/completions` with `gemma4` + image → **400** `This endpoint is currently in beta and not available. To request beta access, please contact our support team`
- `POST /v1/chat/completions` with image content → **400** `body.messages.1.user.content : Input should be a valid string` (v1 is text-only)
- `sarvam-m` is deprecated on this key
- `GEMINI_API_KEY` from `Web/.env` is rejected (`API key not valid`)

No candidate could transcribe a page image. Extraction is stopped per the plan: do not spend the extraction budget, do not hand-write bodies.

Unblock with either Sarvam v2 beta access, or a working Gemini API key.

**Update 12 Sep 2026:** Gemini is out per the user. Switched to Sarvam Document AI (`POST /doc-ai/v1/job/digitise`) — this key can OCR page PNGs. `sarvam-105b` chat cannot emit JSON (finish_reason=length, `content` always null). Parser is therefore deterministic: split OCR on `Q<n>.` and `(1)…(4)`, attach skeleton `figure_keys`. Bake-off 6 pages: 56/56 whitelist. Chapter 5: 14/14 pages, 132/132 questions parsed, 110 published `auto_ok`, 22 MCQs held (option images, no `(1)(2)(3)(4)` text). Confidence 0.5 (single observer). Cost: Document AI pages only.
