---
name: chapter-pyq
description: Use when importing JEE Main chapter PYQs, running OCR-first inventory so no printed question is missed, naming a MathonGo PYQ chapter, reading C:\\Users\\tempo\\Downloads\\Maths session PDFs, adding a new PYQ book, republishing extracted questions, or fixing Chapter PYQ stems, KaTeX, figures, tiers, or /chapter-pyq.
---

# Chapter PYQ

Turn a MathonGo JEE Main PYQ book (or one chapter of it) into published questions on `/chapter-pyq`. The student player already exists. This skill is the **conversion**: extract, map, OCR, format math, publish, verify.

**Web only.** Never edit EduDeca or EduBite. Never commit unless asked. Never revert unrelated waitlist WIP in `Web/middleware.ts`.

## Process order (do not invert)

1. **Scope titles** — catalog slug → every PDF chapter mapped onto it. User said "all" / "every question" / a named TOC count that is several chapters (January **37** = DI+AUC+DE, April **26** printed / named 28) → every printed title in that block. One printed title only when they named one chapter. Done when the title list is written down.
2. **Inventory (no-miss gate)** — `python pyq_ocr_inventory.py --pdf PATH --titles "Definite Integration,Area Under Curves,Differential Equations"`. Match titles on the **full page** (they sit in the footer). Compact Answer Keys span consecutive listing pages — concatenate them. Done when every in-scope title has `printed Q n. == key lines == crop_plan`, and the table is shown. If any chapter fails, stop; do not invent extras. TOC page numbers are not counts.
3. **Crop** — full width, both columns; stitch continuation onto the next page while the same title is still printed; plus that chapter’s key strip. `--crop-dir` or the ingest cropper. Done when PNG count == printed Qs.
4. **OCR packets** — **gemma4** on each crop + key strip. `ThreadPoolExecutor(max_workers=len(jobs))`, cache JSON per Q, retry only failures. Document AI waits. Done when packets == crops.
5. Hold glm solve-match, two-observer, and `auto_ok` until those packets are accepted.
6. Then `format_ocr_math`, KaTeX gate, publish, worked solutions (pyq-solutions, also parallel). Done when `/chapter-pyq` Start, palette, and year-card counts equal publishable `auto_ok|human_ok` rows. Never a fake listed-count.

Paid mistakes: stopping after Definite Integration when the named 37/28 was DI+AUC+DE; scanning only the first 8 lines for titles (AUC lived in the footer → 0 pages); treating TOC “37” as a question count; faking the year card as 67 while the palette showed live 22.

Scripts: `files/pyq_ocr_inventory.py`, `files/ingest_math_2025_di_ocr.py`, `files/ingest_math_2025_auc_de.py` (isolated `out-math-2025-jan-di/` / `out-math-2025-apr-di/`). Named Maths chapters (session PDFs + 2025 booklets in one run): add the chapter to `CHAPTERS` in `files/ingest_math_named_ocr.py`, then `--chapters N` (cache `out-math-<short>/<booklet>/`). Never Gemini.

## Booklet with no printed answer key

Some 2026 PDFs print "Questions with Answer Keys" in the footer but no key. The gate then fails (`keys == 0`). Do not skip the booklet and do not trust one AI answer.

1. Crop and gemma4-OCR each question alone (one image, answer fields null).
2. Two independent glm5.3 solves per question, in parallel.
3. **Open every crop PNG** and re-type the stem from it. OCR can garble a question into a self-consistent wrong one (Seq 2026 Q17 lost `\sum_{n=1}^{40}` and `\frac{3^\alpha-1}{3^\beta}`; one solve picked a wrong option from that text).
4. Solve every question yourself. Publish `human_ok` only when your answer is settled; agreement between two solves is a hint, not a key.
5. Tell the user these keys are solved, not official, and name any you could not settle.

Done when every printed Q has a crop-typed stem and a key you verified. Then solutions (pyq-solutions), where the same rule applies: read every step.

## Before any work

Copy this checklist and fill the blanks. Do not extract until the user confirms the blanks you cannot infer.

```
Source
- [ ] PDF path: (Maths → [maths-folder.md](maths-folder.md); never upload the folder)
- [ ] If math session PDF: question-page range (stop before Answer Key / ANSWERS AND SOLUTIONS)
- [ ] Subject: physics | chemistry | math
- [ ] PDF chapter no / title:
- [ ] Page range (inclusive):
- [ ] Catalog slug (from pdfChapterMap / catalog):
- [ ] Merge-as-topic? (no new route) or new catalog chapter?
- [ ] Deferred? (straddles two catalog chapters → stop)

Scope (fill this first — do not invent a pilot)
- [ ] One chapter  OR  whole book/subject
- [ ] If the user said "all", a subject name, or "every question": whole book. Do not stop after one chapter.
- [ ] In-scope printed titles (catalog map or named TOC block):

Inventory (no-miss — before OCR spend)
- [ ] `python pyq_ocr_inventory.py --pdf PATH --titles "..."` gate_ok
- [ ] Per title: printed Q n. == Answer Keys == crop_plan
- [ ] Full-page title match (not first 8 lines)

Done when
- [ ] Skeleton rows exist for every chapter in scope
- [ ] Figures uploaded; Storage GET 200 (skip only if the chapter has no real rasters)
- [ ] Bodies + options written
- [ ] Publishable rows are review_status auto_ok | human_ok
- [ ] Image-option MCQs held (unreviewed)
- [ ] `python audit_paper_text.py` is clean on the parsed set in scope
- [ ] Stems render with $KaTeX$ and paper-white figures
- [ ] Published stems/options have no overlay OCR (`mathongo`, `# # mi`, trailing `mi`)
- [ ] `/chapter-pyq` list shows live counts for every catalog slug in scope
- [ ] `/chapter-pyq/<subject>/<slug>` Start, palette, and year-card counts match publishable rows
```

Read these only as needed:

- Mapping + catalog: `Web/lib/chapter-pyq/pdfChapterMap.ts`, `catalog.ts`
- Spec / plans: `Web/docs/superpowers/specs/2026-09-11-chapter-pyq-physics-import-design.md`
- Scripts: `c:/Users/tempo/Downloads/files/` (`pyq_ocr_inventory.py`, `pyq_common.py`, `run_chapter_agents.py`, `extract_assets.py`, `build_skeleton.py`, `extract_ocr.py`, `parse_ocr_page.py`, `format_ocr_math.py`, `write_and_publish.py`)
- Math add-on: [latex-katex.md](latex-katex.md)
- Maths folder (session PDFs, 29 TOC, leftover chapters): [maths-folder.md](maths-folder.md)
- New book / new subject: [new-book.md](new-book.md)

## Hard rules

| Rule | Reality |
|---|---|
| Tiers | Copy book headings `MUST DO` / `CONCEPT BUILDER` / `ADVANCED`. Never invent difficulty. |
| Topics vs chapters | Physics may merge PDF chapters onto one catalog page. **2025 Jan/Apr Maths is 1:1 with that booklet’s 29 TOC numbers** — never use the 33-chapter compilation map (it inserts extra chapters and shifts DI to 19). Footer “Trigonometric Ratios” is still TOC ch.25. |
| Type / chapter columns | Follow `.cursor/rules/question-bank-docx-type.mdc`. Never put a chapter name on `type`. |
| Numericals | Real numeric input. Never `buildNumericMcq`. `options: []`, `correctAnswer: -1`, score via `isPyqAnswerCorrect`. |
| MCQ keys | `correct_option` membership is `{"1","2","3","4"}`. `"12" in "1234"` is a substring true — it rejects multi-select keys. |
| Students see | `review_status in ('auto_ok','human_ok')` only. Paper-only stems and options. |
| KaTeX gate | After ingest, recheck every published stem **and option** with KaTeX. Leftover `$`, raw `\frac` / `\sqrt` / `\in` / `\mathbb` outside `$…$`, smashed `int`/`rac`/`ext` (eaten `\int`/`\frac`/`\text`), GIF `[x]` / `[a,b]` that fail to render, or solver text in the stem (`The answer is`, `\boxed`, worked solution) → hold. Never `human_ok` those rows. Shape-valid is not enough. |
| Overlay | Drop overlay OCR from every stem and option: `\bmathongo\b`, `# # mi`, trailing `mi` after page digits (`3π/4 16 4 4 mi` → `3π/4`). `format_ocr_math` and `cleanPyqOcrText` both strip; `audit_paper_text.py` must be clean. Never put those tokens on `/chapter-pyq`. Never name the overlay in student UI or in chat — talk about the question. |
| Worked solutions | **REQUIRED SUB-SKILL:** pyq-solutions. After a stem rewrite, regen that row’s `solution_md` **first**. Tips / Formula's (`tips_md` / `formulas_md`) run only after that solution exists — glm JSON from question + stored solution, never a chat paragraph. Popup wrap, empty boxes, scrollbar, shredded GIF/interval sentences, or a title-only modal are parser/UI — do not call glm. |
| Models | Primary text solver: `glm5.3`. Fallback if GLM is empty: `deepseekv4-flash`. Vision observer: `gemma4`. Vision tie-break: `glm5.3-flash`. Layout OCR: Document AI. `/v2/chat/completions` only. **Not Gemini.** Never quote accuracy. Conductor: `python run_chapter_agents.py --book math --chapter N` (Mathematics `out-math/`) or `--chapter N` (Physics `out/`). |
| Whole book | If the user asked for a subject / "all questions" / the PDF: digitise **every question page**. A one-chapter run is only when they named one chapter. v1 conductor is chapter-scoped; looping chapters is a later flag. |
| `/chapter-pyq` | After every publish, check the list and the chapter page. Login wall ≠ "skipped check" — then verify publishable counts in DB and say the browser could not sign in. |
| Figures | Stem keys `p{page:03d}_x{xref}` stay immutable. Solution sketches use `sYYYYm_…_qNN_N` (`RASTER_KEY`). Class `nta-mock-img` — never dark-invert. Never Type-3 equation ink. Maths session rules: [maths-folder.md](maths-folder.md). |
| `auto_ok` today | Two observers agree **and** `glm5.3` matches the PDF key (`extraction_confidence = 1.0`). DeepSeek is not a peer vote — it only counts when GLM returned nothing. Single-observer stays `0.5` and is not `auto_ok`. Do not quote accuracy. |
| Shell | PowerShell. No `&&`. Set `$env:PYTHONUTF8 = "1"`. Python `C:\Python314\python.exe`. Pin `pymupdf==1.26.3`. |
| DB | Web / TestBee project `bytsiknhtcnlxwzgqkrd`. Tables `pyq_*`. Bucket `pyq`. |

## Caches — never mix subjects

| Subject | Folder |
|---|---|
| Physics | `files/out/` |
| Mathematics | `files/out-math/` |

OCR JSON lives in `<folder>/ocr/page_NNN.json`. Re-use the cache; do not re-pay a completed page. Do not write Maths rasters into Physics `out/`.

## Run (user asked for a whole subject or "all questions")

This is the default when they did **not** name one chapter.

1. Say the scope out loud: e.g. "Mathematics PDF, 33 chapters, every question page, Sarvam digitise."
2. Skeleton + answer key for the **whole** PDF (₹0). Gate: skeleton count = answer-key count.
3. Rasterize every page that has at least one question. Digitise each PNG. Resume from cache.
4. Seed every PDF chapter onto its `catalog_slug` (merge-as-topic rows share a slug; no extra route).
5. Parse keyed by `(chapter_no, q_no)` — `q_no` restarts every chapter; a flat `parsed[q_no]` will smash later chapters.
6. Publish shape-valid rows. Hold the rest. Do not quote accuracy.
7. Audit the **full** parsed set.
8. Bump `chapter-pyq-questions-vN` and `chapter-pyq-counts-vN`.
9. Check `/chapter-pyq` (subject tab + a live chapter + one still-empty chapter if any).

Maths rasters are rare (most diagrams are vectors). Do **not** crop Type-3 equation ink as figures — those look like smashed stems plus the watermark. Only `p{page:03d}_x{xref}` rasters, or a later measured vector pass.

## Run (existing Physics book, next chapter)

Pilot already landed: Laws of Motion, PDF ch.5, pages 47–60. Skeleton for all 4115 Physics questions exists. For the next Physics chapter:

1. Resolve `catalogSlug` via `catalogSlugForPdfChapter`. If `null` (ch.17 Electrostatics) → stop and say it is deferred.
2. Confirm pages + question count from `files/out/skeleton.json` (or `PROGRESS.md`).
3. Prefer `python run_chapter_agents.py --chapter N` (parallel Document AI, `gemma4` observer, optional `glm5.3-flash` tie-break, KaTeX probe, `glm5.3` primary solver, `deepseekv4-flash` only if GLM is empty). It uploads that chapter's `p{page:03d}_x{xref}` keys, GETs them, and stops on `hold.json`. Do not invent a new key scheme.
4. OCR cache stays `files/out/ocr/page_NNN.json`. Re-use it; do not re-pay a completed page.
5. Parse still splits on `Q<n>.` and `(1)…(4)` via `parse_ocr_page.py` + `format_ocr_math.py`.
6. Skip OCR blocks tagged `chart|figure|image` and any block starting with an image-caption phrase. `format_ocr_math` / `cleanPyqOcrText` cut leftover captions, tables, `**`, overlay OCR.
7. `auto_ok` only when two observers agree and `glm5.3` matches the PDF key. Hold MCQs with no `(1)(2)(3)(4)` text (option-as-image). Apply user decisions with `--apply-holds hold.json`.
8. Place `[[fig:KEY]]` from the skeleton's `figure_keys` after cleanup (cleanup must not swallow the token).
9. Bust the questions API cache (`chapter-pyq-questions-vN` or `revalidateTag`), then hard-refresh `/chapter-pyq/physics/<slug>`. Player “Question 5” is the 5th item in the **set**, not PDF `q_no` 5.
10. **Audit the whole chapter, not the screenshots.** Run `python audit_paper_text.py --parsed out/agents/chapter_N/parsed.json`. Caption/`**`/table/overlay/heading/empty-option hits must be zero before you tell the user it is clean. Truncated `√` in an otherwise real option is leftover OCR glyph loss — hold only if the option is unanswerable (`""`, `"√"`, `"N"`, or a lone page number).

Generalize scripts that still hardcode `CHAPTER_5` before running them on another chapter. Prefer a chapter-no argument over a copy-paste fork.

## Run (user names only a catalog chapter)

Example: “do Work Energy and Power”.

1. Find the catalog slug (`work-energy-and-power`).
2. List every PDF chapter mapped onto it (`pdfChaptersForCatalogSlug`).
3. Import **all** mapped PDF chapters onto that one page (merge-as-topic).
4. Tell the user the PDF titles that will land as topics, then run.

## Add-ons (always apply)

These are part of the conversion, not extras to skip.

1. **LaTeX / KaTeX** — [latex-katex.md](latex-katex.md). Every stem/option that contains math must reach the player as `$…$` inside `<p class="nta-math-plain">`.
2. **Paper figures** — `img.nta-mock-img` stays white-on-print. Dark-mode invert excludes that class (`Web/app/globals.css`).
3. **Paper-only text** — stem = printed question; then the figure; then the four printed options. Never persist Document-AI captions, invented tables, `**`, overlay OCR (`mathongo`, `# # mi`, `16 4 4 mi`), book headings (`MUST DO PROBLEMS`, `Spring force`, …), page-number tails (`75N 49` → `75N`), or `ball (a)ball (b)` figure labels. Strip those from **options** too. Physics page tails are not enough — Maths uses other page numbers. The PNG is the figure; the caption is not the question.
4. **Hold unanswerable MCQs** — missing `(1)(2)(3)(4)`, blank options, lone `√`/`N`, or a two-digit page number as the whole option. After every republish, bump `chapter-pyq-questions-vN`. **Always audit every question in the chapter** (`audit_paper_text.py`); do not stop after the rows the user screenshotted.
5. **Sets** — `max(1, round(total/25))` sets, sizes differ by ≤1, 2 min/question. Filter tier first, then split. Mathematics year chips are **2021–present** (investor: 2020 not required), newest year first, January before later months, year-only. Start / palette / header = live publishable items; never a fake listed-count.
6. **Undated tags** — leave `exam_date` null; put them in `manual_review.json`. Never guess a date.
7. **Maths session PDFs** — [maths-folder.md](maths-folder.md). Split questions / keys / solutions. Never `get_text` formulas. Never leftover LCD / Heights / Reasoning folders onto the 29 TOC.

## Display path (already built — reuse)

- Mapper: `Web/lib/chapter-pyq/pyqQuestionMap.ts` → `pyqStemToHtml`
- Figures: `pyqFigures.ts` emits `<img class="nta-mock-img">`
- Player: `ChapterPyqExamSession` + NTA shells. After submit, `ChapterPyqResultView` scores from the mapped answer key (`correct_option` / `numerical_answer`) the same way mocks do: expand a row for stem, options, your pick, and correct.
- Solution popup: `NtaSolutionModal` + `NtaWorkedSolutionSheet` + `parsePyqWorkedSolution`. Tips / Formula's: `NtaCoachSheet`. Layout and coach JSON live in pyq-solutions.
- Reads: service-role API `Web/app/api/chapter-pyq/questions` and `counts`
- Vitest is node-only (`lib/**`, `app/**`)

Do not import `MockPageContent`. Do not use jsdom.

## Red flags — stop

- Using Gemini because “OCR is OCR”
- Inventing a tier or a catalog chapter to make the mapping tidy
- Creating a route for a merge-as-topic PDF chapter
- Publishing a 4-option MCQ whose options are blank / “(OCR missed”
- Leaving overlay OCR (`mathongo`, `# # mi`, trailing `mi`) on a published stem or option
- Inverting PYQ figures in dark mode
- Committing, or touching EduDeca / EduBite
- Quoting extraction accuracy (single-observer or two-observer)
- Stopping after a pilot chapter when the user asked for the whole book or subject
- Telling them Maths (or any subject) is "done" if only one chapter was digitised
- Skipping the `/chapter-pyq` list + chapter-page check after publish
- Regenerating `solution_md` to fix wrap, empty formula boxes, or shredded `[x]` / `[a,b]` (that is parser/UI — pyq-solutions)
- Leaving old `solution_md` after rewriting a stem
- Setting `white-space: normal` on `.katex-display > .katex` (splits intervals at the comma)
- Trusting TOC page numbers instead of the printed chapter title + Answer Keys count
- Scanning only the first N lines for chapter titles (titles sit in the footer)
- Stopping inventory after the first running title when the named count or catalog slug maps to several chapters
- Faking a year-card listed-count instead of live publishable rows
- Running Document AI or glm before the per-question gemma4 OCR packets exist
- Serialising OCR or solutions one question at a time in chat
- Uploading `C:\Users\tempo\Downloads\Maths` (or a whole session PDF) without splitting questions / keys / solutions
- Publishing Maths `page.get_text` as a stem (fractions are shredded)
- Sourcing `Limits, Continuity and Differentiability\` onto Limits or C&D
- Numbering 2025 Jan/Apr Maths from the 33-chapter compilation book
- Publishing a no-key booklet on two AI solves agreeing, without opening the crops and solving it yourself
- Reading `15. 08` (a decimal) as question 15 — `session_q_anchors` skips a `n.` line followed by a digit
