# Chapter PYQ — new book or new subject

Use this file when the PDF is not the Physics MathonGo book already skeletoned at `files/out/skeleton.json`.

## Decide the branch

| Situation | Do |
|---|---|
| Same Physics PDF, next chapter | Stay on `SKILL.md` “existing Physics book” |
| New PDF, same subject (e.g. Chemistry MathonGo) | This file, then run conversion per chapter |
| New subject in the app catalog | Add catalog names **syllabus-ordered** (not alpha), then this file |
| PDF chapter straddles two catalog chapters | Defer. Do not guess a split. |

## OCR first (before Phase 0 agents)

Session / chapter-wise Maths PDFs live under `C:\Users\tempo\Downloads\Maths` — [maths-folder.md](maths-folder.md). Run `python pyq_ocr_inventory.py --pdf PATH --titles "..."` so **every** in-scope printed title is inventoried (catalog map, or the named TOC block such as Jan 37 = DI+AUC+DE). Inventory **question pages only** (stop before Answer Key / ANSWERS AND SOLUTIONS). Match titles on the **full page**. Concatenate consecutive compact Answer Keys pages. Gate: `printed Q n. == key lines == crop_plan` per title. Then crop (full width, stitch continuation on the same title) and **gemma4** on those packets in parallel. Document AI and glm solvers wait until packets == crops. See the process-order block at the top of `SKILL.md`. TOC page numbers are not counts. Never `get_text` the formula layer.

## Phase 0 — machine

- Python `C:\Python314\python.exe`
- `pymupdf==1.26.3` (newer `_mupdf.pyd` is blocked by Windows Smart App Control)
- `files/.env` copied from `Web/.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SARVAM_API_KEY`
- Leave `GEMINI_API_KEY` unused even if present
- Primary text solver: `glm5.3`. Fallback if GLM is empty: `deepseekv4-flash`. Vision OCR (stems): `gemma4` on per-question crops. Vision tie-break only after OCR is accepted: `glm5.3-flash`. Document AI is not first.

## Phase 1 — whole book, no AI

Scripts: `extract_assets.py`, `build_skeleton.py`.

Outputs (immutable once accepted):

- `out/skeleton.json` — one row per question
- `out/answer_key.json`
- `out/figures.json` + `out/figures/*.png`
- `out/pages/page_NNN.png`
- `out/orphan_figures.json`

Figure key: `p{page:03d}_x{xref}`. If two images share a page+xref collision, extend with a documented suffix — do not change the scheme for older keys.

Watermark: skip images covering >85% of both page axes.

Rebuild `TIER_MAP` / fonts only after inspecting the new PDF's text layer. MathonGo Physics used:

- Chapter: `FiraSans-ExtraBold` ~20 / ~40
- Tier: `FiraSans-ExtraBold` ~11.2 (`CONCEPT BUILDER` / `MUST DO` / `ADVANCED`)
- Topic: `TimesNewRomanPS-BoldItal` ~11.2

If this book has no tier headings, leave `tier` null and hide the chips. Do not invent Must Do.

## Mapping

1. List PDF chapter titles in reading order.
2. Map each to a catalog slug (`1:1`, rename, merge-as-topic, new catalog chapter, or `null` deferred).
3. Get user sign-off on the map **before** creating routes.
4. Persist the map next to `pdfChapterMap.ts` (or a sibling for chemistry/math).

`pyq_chapters.name` = coarse PDF title. `pyq_topics.name` = fine heading. `catalog_slug` is not unique.

## Schema / seed

Migration already exists for Physics: `Web/supabase/migrations/20261019120000_pyq_question_bank.sql`.

For a new subject: add `pyq_subjects` / units / chapters / topics via `seed_taxonomy.py`. Do not create a parallel unprefixed `questions` table.

Students still only read `auto_ok` / `human_ok` through the service-role API.

## Then convert one pilot chapter

Pick a 1:1 catalog chapter that has figures (so the figure path is real). Run the `SKILL.md` chapter checklist on that chapter only. Do not OCR the whole book until the pilot page looks right in the player.
