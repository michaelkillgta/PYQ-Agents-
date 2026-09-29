---
name: pyq-solutions
description: >-
  Use when writing or repairing Chapter PYQ NTA solutions, Tips, Formula's,
  tips_md/formulas_md coach JSON, a MathonGo solutions PDF, paper OCR write-ups,
  2026 step cards, parallel OCR/partition, popup wrap/wavelength, listing
  headers like 12. (3), PDF image xref figure upload,   crop-vs-popup
  cross-check, C:\\Users\\tempo\\Downloads\\Maths session PDFs (ANSWERS AND SOLUTIONS
  section), run_pyq_solutions.py, or generate_di_coach.py.
---

# PYQ Solutions

Worked solutions for `/chapter-pyq`. **Web only.** Never EduDeca / EduBite. Never commit unless asked. Never quote accuracy.

**REQUIRED BACKGROUND:** chapter-pyq (stems, keys, figures) and [maths-folder.md](../chapter-pyq/maths-folder.md) when the source is `Downloads\Maths`. This skill does not ingest question stems. Never upload a session PDF whole — crop only the **ANSWERS AND SOLUTIONS** / footer **Solutions** band.

## Process order (do not invert)

1. **Solutions first** — paper OCR packet or glm sheet on `solution_md` for every in-scope publishable row. Done when the Solution popup shows that write-up.
2. **Then Tips and Formula's** — glm5.3 reads that stored solution + the question and writes `tips_md` / `formulas_md`. Done when TIPS and FORMULA'S parse as move cards. Never start coach JSON on a row with empty `solution_md`.

User named only Solution → stop after step 1. User named Tips / Formula's → still finish step 1 on any row that lacks a solution, then step 2. Both in one ask → same order, one run after the other, not mixed in the same glm call.

## Before any work

Copy and fill. Do not call a model until the blanks the user named are set.

```
- [ ] Subject: physics | math
- [ ] Catalog chapter / PDF chapter_no:
- [ ] Year (e.g. 2026)  OR  whole chapter (all years)
- [ ] Job: Solution  OR  Tips/Formula's after solutions exist  OR  both (solutions, then coach)
- [ ] Source PDF (Maths folder path): 
- [ ] Solutions start page (heading ANSWERS AND SOLUTIONS or footer Solutions — not the Q pages, not footer “Answer Keys”)
- [ ] Printed solutions in that band? yes → follow the paper. no → glm sheet
- [ ] `solution_md` already on every in-scope row? if no, write solutions before coach
- [ ] Overwrite existing solution_md? no unless asked
- [ ] Overwrite existing tips_md / formulas_md? no unless asked
```

Named year only → that year. Whole chapter named → every publishable question in that chapter, **one worker per question**, same run.

**Pick one path and stay on it:**

| Situation | Path |
|---|---|
| User names a Maths session PDF / chapter folder, or a MathonGo **solutions** band (`ANSWERS AND SOLUTIONS` / footer `Solutions`), or the row already has `<!-- paper-ocr -->` | **Follow the paper** below. gemma4 only. Crop from that heading, not from Q1. |
| Popup wrap, glued labels, mid-formula break, listing `12. (3)`, shredded sentence, step title `$\\mu$`, footer chip showing option `1` instead of `16` | Fix `pyqOcrHtml.ts` / `NtaWorkedSolutionSheet` / `polishWorkedSolution` / CSS. Vitest first. Leave stored letters unless they disagree with the printed page. |
| No printed write-up, and the algebra is wrong | `run_pyq_solutions.py --overwrite` (glm JSON sheet) |
| User asks for **Tips** / **Formula's** | Confirm `solution_md` is already on those rows. If missing, **Follow the paper** or glm sheet first. Only then **Tips and Formula's**. |

A paper packet is never glm-overwritten after a stem repair.

**Parallel — fill the booklet in one run.** Many questions, little wall-clock: `ThreadPoolExecutor(max_workers=len(jobs))` on OCR, partition, figure extract/upload, then glm solve. Coach JSON is a **later** pool on the same rows, after `solution_md` is stored. One worker per question, same process. Retry only failures. Never serialize Q-by-Q in chat. Never glm tips in the same call as the solution sheet.

---

## Follow the paper (printed write-up already exists)

The booklet **is** the solution. Transcribe it, **partition** it into step cards, render it the way the page is printed. Do not write a new solution, do not glm, do not re-OCR a packet that already matches the page.

January 2026 Definite Integration is the reference run: `solution_md` starts with `<!-- paper-ocr -->`. Popup: `ntaQuestionSolutionText` → `pyqSolutionToHtml` → step cards → `NtaRichTextBlock`.

### Done when

Every in-scope printed Q has a paper packet, each crop matches the popup line-for-line (including lines next to sketches), listing headers and watermarks are gone, figures are PDF xrefs, Vitest for renderer changes is green, and `CHAPTER_PYQ_CACHE_VERSION` is bumped.

### Steps

1. Inventory the solutions PDF (printed Q n. == key lines == crop_plan). Stop on mismatch.
2. gemma4 OCR **all** solution crops + key strips in one parallel pool (`max_workers=len(jobs)`). Cache JSON per Q. Retry only missing/failing crops.
3. Assemble `<!-- paper-ocr -->` markdown. Strip listing `n. (key)`, watermarks, page-crop `[[fig:…_crop]]`. `[[fig:]]` only for a real graph/sketch.
4. **Partition** all packets in one parallel text-only gemma4 pool (titles + line ranges). Every original line covered once. Headings are new; letters stay.
5. **HARD GATE:** open every crop PNG vs the packet (see below). Fail if stacked equals became a nested fraction. Not one screenshot of Q1. Not PDF `get_text`. Not OCR JSON. Not a vision “missing lines” dump.
6. Only then publish `solution_md` and bust `CHAPTER_PYQ_CACHE_VERSION`.

```
cd c:\Users\tempo\Downloads\files
$env:PYTHONUTF8 = "1"
C:\Python314\python.exe ingest_math_2026_jan_di_solutions.py
C:\Python314\python.exe layout_math_2026_jan_di_steps.py
```

Isolated cache: `files/out-math-2026-jan-di-solutions/`. Next booklet: copy that pair of scripts, new `OUT` folder, same gates. Never send solution PNGs to glm.

### Multi-page write-ups

A printed solution that runs onto the next page is **one packet**. Inventory sets `continues` and `render_crop` **stitches** the leftover band (until the next `n.` heading) onto the same PNG. gemma4 OCRs that stitch, so page 2 text is not dropped. If a write-up still continues after that band, extend the crop plan — do not OCR page 1 alone.

### How to take solution images (PDF object, 2025 reference)

Crops are **OCR input only**. Students never see the page raster. A real graph/sketch is a separate PNG from the PDF **image xref**.

**Take**

1. Clip = that Q’s `crop_plan` (`y0` / `clip_y1` / continuation band).
2. `page.get_image_info(xrefs=True)` inside the clip.
3. Skip full-page marks: both `w` and `h` > 0.85 of the page. Skip hits under 24pt.
4. **Every remaining xref**, reading order (top then left), is its own PNG: `Pixmap(doc, xref)` → `{key}_1.png`, `_2`, `_3`, …. **Never keep only the largest.** A question with three printed graphs must have three tokens. **Never** `page.get_pixmap(clip=bbox)` (bakes leftover page text into the figure).
5. Token `[[fig:sYYYYt_…_qNN_N]]` on its own line **where that drawing sits**. Typeset math next to a sketch stays markdown (2025 Jan DI Q7: `$=(x-4)x(x-5)$`; 2024 Apr DI Q1 piecewise next to the small triangle).
6. Drop listing `7. (4)` / `Q1` on that line; keep the formula.
7. Before publish: count xrefs in the clip vs `[[fig:]]` tokens. If they differ, a sketch was dropped.

**Upload (all figures, one pool)**

```
ThreadPoolExecutor(max_workers=len(jobs))
→ pyq/math/figures/{key}.png
→ public GET 200 and GET bytes == local bytes
```

PyMuPDF: one `Document` per worker (do not share a doc across threads). New filename when replacing bytes (`_1` → `_2`); upsert of the same key often still serves old bytes. Then swap live `[[fig:]]` and bump `CHAPTER_PYQ_CACHE_VERSION`.

Code: `extract_figure` + `upload_one_figure` in `ingest_math_2025_paper_solutions.py`. Re-run extract+upload: `upload_2025_xref_figures.py`. Renderer keys: `RASTER_KEY` in `Web/lib/chapter-pyq/pyqFigures.ts` (`s2025j_di_q07_2`, `s2025apr_te_q03_1`, `s2026_te_q01_1` must match). Click-to-enlarge is `NtaFigureLightbox` — ingest does not add it.

Tiny native bitmap (2025 Jan DI Q4 wavy curve ~281×85): redraw SVG then rasterize. Do not upscale the xref.

### HARD GATE — crop vs packet (cannot skip)

Do not say solutions are done, do not publish `solution_md`, and do not bump `CHAPTER_PYQ_CACHE_VERSION` until **every** in-scope printed Q has had its **crop PNG opened** and walked against the stored packet line by line.

The crop is the layout source. gemma4 OCR JSON is not. A popup screenshot of one Q is not a chapter check. Vision “missing lines” dumps are not.

**Stacked printed equations stay stacked.** If the page has

```
A / B  =  C
D / E  =  F / G
```

that is two display lines. Never glue them into one nested `\frac{\frac{A}{B}}{\frac{D}{E}}=\frac{C}{\frac{F}{G}}`. OCR does this constantly on two-row identities (2026 TE Q2).

Also fail the gate if: a minus became a plus; an interval `[0,2\pi]` became `(0,2\pi)`; `\pm` dropped; leftover `Solutions` / Marks-app / next-chapter algebra from a polluted crop was ingested; quadratic-formula lines were invented that are not on the page; glm/OCR write-up disagrees with the crop (C&D 2024 Apr Q7 LHL was not `\tan x/\tan 7x`); `katex_render` hold on a paper packet — fix letters from the crop, do not skip the row.

**glm JSON sheet (no paper band):** step `title` strings go through KaTeX (`NtaSolutionKatex`), never a raw `<h3>`. Footer chip is `polishWorkedSolution`’s computed value (`16`, `K=1`), not the MCQ option index when `answer` is `1`–`4`. After you repair `solution_md`, regenerate that row’s Tips/Formula’s (`generate_pyq_coach.py --overwrite --ids`).

Fix from the crop. Then partition (titles only). Then bust cache.

### How to cross-check (every Q, before you say done)

Open **that Q’s crop PNG** (stitched if `continues`) next to live `solution_md` / the NTA popup. Walk top to bottom.

| Check | Pass |
|---|---|
| Every printed line | In the packet, same order. Continued-equals under a sketch (`$= (x-4)x(x-5)$`) is text, not “covered by the figure”. |
| Two-row equals | Two printed identities remain two KaTeX lines, not one nested fraction. |
| Letters | Signs, `\pm`, intervals, and substitution (`9/t+t=10` not `+10=10`) match the crop. |
| Sketch | Popup image is the xref PNG (no page text). **Every** printed graph has a token, in order. |
| xref count | `get_image_info` hits in the clip == `[[fig:]]` count. One token for three graphs is a miss. |
| Storage | Public GET bytes match the file you uploaded. New key if you replaced bytes. |
| Renderer | Token matches `RASTER_KEY`; figure actually shows (not swallowed `[[fig:]]`). |
| Listing / marks | No `7. (4)`, no page title, no MathonGo, no next-section leftover in student HTML. |

**Do not use as the check:** PDF `get_text` on these booklets (fractions/watermarks shred). A gemma4 “list missing lines” JSON (it invents latex — 2025 repair had to revert 10 packets). One screenshot of Q1. OCR JSON fraction structure.

Partition still runs on the full packet (page 1 + continuation + figure tokens), so step cards cover the whole write-up.

### Partition (`## Step N: Title`)

gemma4 returns `{steps:[{title,start,end}]}` covering every line in order. Rebuild:

```
<!-- paper-ocr -->

## Step 1: Decomposition
<verbatim lines>

## Step 2: …
```

Titles are 2–6 words (Decomposition, Symmetry, Substitution, Integration, Final evaluation). Heuristic cuts only if coverage fails. Assert rebuilt lines == original lines.

Renderer: `Web/lib/chapter-pyq/pyqOcrHtml.ts` (`paperStepsToHtml`). CSS: `.nta-paper-steps` in `Web/app/globals.css`. Tests: `pyqOcrHtml.test.ts`.

### Match the printed line

Read the page. Put each phrase where the page puts it.

| On the page | In the popup |
|---|---|
| `Let F(x) = …`, `Zeros in [0, π]: …`, `Using … = …`, `Total = …`, `Expression is positive on (0, π/2), negative on …` | **One line.** Label stays on the formula. |
| `Now \|4x−π/12\| = { row ; cond` two stacked rows | **Piecewise.** `Now` sits in `$$\text{Now }…\begin{cases}$$` left of the brace. Never inline `$cases$` — nowrap shreds the brace and drops `Now` below it. |
| `By IBP:`, `By parts`, `Applying King` then a working integral | Label **above**. Formula is display `$$`, full width of the step (**wavelength**). |
| Stacked `\frac{\sec^6\theta}{\tan^6\theta+1}` | **One** integral. Numerator and denominator are not two `\int` lines. |
| `12. (3)` / `14. (64)` at the start of the write-up | **Drop it.** Question number and key already sit on the exam chrome. Keep the following word (`From`). |
| `h(x)=\{ x-2+2-x=0,\ \ldots` printed cases | **Keep the printed algebra.** Never collapse to `h(x)=0 for 0≤x≤2`. |
| Three graphs on one write-up | Three `[[fig:]]` tokens. Never one combined clip. |
| A long working line | One wavelength: `white-space: nowrap` + `overflow-x: auto` on the step body. Never wrap inside `\int` / `\frac`. |

Code already encodes this: `shouldJoinPaper` / `METHOD_ABOVE` / `PAPER_LISTING_PREFIX` / `PAPER_STACKED_ENV` / `.nta-paper-step-body .katex { white-space: nowrap }`. Wavelength nowrap is for **one printed working integral** and for **cases rows**. Never set `.mtable { white-space: normal }` — that wraps `{` columns into a shredded brace. Extend those, do not special-case one question in chat.

Full-page crops are OCR input only. Students never see MathonGo watermarks.

---

## glm JSON sheet (no printed write-up)

```
cd c:\Users\tempo\Downloads\files
$env:PYTHONUTF8 = "1"
C:\Python314\python.exe run_pyq_solutions.py --book math --chapter 19 --year 2025
```

`--dry-run` prints the packet and writes nothing. `--overwrite` replaces stored `solution_md`.

1. Load publishable row: stem, options, official key, figures.
2. Figure raster → **gemma4** markdown. **glm5.3 must not see a PNG.**
3. One markdown packet: question + figure MD + options + official key.
4. **glm5.3** JSON: `title`, `problem_tex`, **4–8 steps** in `phases[]` with ordered `blocks`. Not a numbered dump and not two blobs named Setup/Working.
5. 429 / 502 / 503 / timeout → retry. Wrong `answer` → retry up to 4 with the official key restated.
6. Write only when `should_write_solution` is true. Hold the rest.
7. Bust `CHAPTER_PYQ_CACHE_VERSION`.

After a stem repair, regen **only the rows whose stem changed** — except `<!-- paper-ocr -->` rows; those stay paper.

---

## Tips and Formula's (coach notes)

Beside Solution the player has **TIPS** and **FORMULA'S**. They are not the worked write-up. Store them on `pyq_questions.tips_md` and `formulas_md`. glm5.3 reads the **printed question + stored solution** and returns JSON. Never invent a glued KaTeX paragraph in chat.

**Gate:** skip any row whose `solution_md` is empty. Fill solutions first (paper path or glm sheet), publish, then run coach. Tips without a solution are blocked.

### Done when

Every in-scope publishable row has parseable JSON (`parsePyqCoachTips` / `parsePyqCoachFormulas`), 3–5 tip **moves** from that solution, 2–5 identities actually used, no leaked key, NTA/JEE wording, and `CHAPTER_PYQ_CACHE_VERSION` is bumped.

### JSON glm must emit

```
{"tips":[{"title":"2 to 5 words","body":"$KaTeX$ sentences","callout":"optional boxed $identity$"}],"formulas":[{"name":"NCERT/JEE name","tex":"latex, no dollar signs","note":"when to use, under 12 words"}]}
```

- Tips: 3–5 moves in think-order from **this** solution (split, odd/even, King, GIF slab, \(x\to a+b-x\), substitute). One move per card. Optional `callout` is one identity for that move, never the last boxed number.
- Formulas: 2–5 identities that solution uses. One identity per card.
- Never the numerical, option `(1)`–`(4)`, or `\boxed` line.
- NCERT Class 12 Integrals / JEE Main names (King property, GIF, odd/even). Write `\pi` not `\rho`.

### Run

Rows with no `solution_md` are out of this pool. Write those solutions first, then come back.

```
cd c:\Users\tempo\Downloads\files
$env:PYTHONUTF8 = "1"
C:\Python314\python.exe generate_di_coach.py --years 2023,2024,2025
```

Any Maths chapter: `generate_pyq_coach.py --chapters N --years 2026 [--ids uuid,uuid] [--overwrite]`. It reads `files/out-math-pyq-coach/glm/{id}.json` first, so `--overwrite` alone republishes the **old** notes. After a solution rewrite, delete those cache files, then run with `--overwrite --ids`.

`--overwrite` replaces stored coach JSON. Default skips rows that already have `tips_md`. Isolated cache: `files/out-math-di-coach/glm/{id}.json`. 2026 DI used `generate_2026_di_coach.py` / `out-math-2026-jan-di-coach/`. Next chapter: copy the generator, new `OUT` folder, same gates. **glm5.3** text-only. Never a PNG.

`ThreadPoolExecutor(max_workers=len(jobs))`. Retry only failures. **Publish every valid cache even if two blobs fail.** Truncated `formulas` → repair from the tips/callouts. Empty `{options:null}` → delete that cache file and glm again.

Validate in `generate_di_coach.py`: ≥3 tips, ≥2 formulas. Drop a card that leaks the key or uses Fredholm / Lebesgue / Hilbert / Banach / IMO / A-level / AP Calculus.

### UI (reuse — do not invent a third sheet)

| Piece | File |
|---|---|
| Parse | `Web/lib/chapter-pyq/pyqCoach.ts` |
| Tests | `Web/lib/chapter-pyq/pyqCoach.test.ts` |
| Map | `pyqQuestionMap.ts` → `coachTips` / `coachFormulas` |
| Wire | `ntaQuestionCoachText` → `NtaExamShell` TIPS / FORMULA'S → `NtaSolutionModal` `panel` |
| Tips look | Derivation Path timeline, Move N, neon track, `.nta-coach-callout` — `NtaCoachSheet` `TipsBlueprint` |
| Formula's look | Formula Codex, REF. 01, sanctuary chamber — `NtaCoachSheet` `FormulaCodex` |
| CSS | `Web/app/globals.css` `.nta-coach-blueprint` / `.nta-formula-codex` |

A dense paragraph in the popup means the row is old prose, not glm JSON — regenerate with the generator, do not restyle around a blob.

### Audit

For every in-scope year: JSON parses; moves match the printed/glm solution; last tip is not the option; `\pi` not `\rho`; no university-course names. Check the year, not only Q1.

## NTA Solution popup (reuse)

| Piece | File |
|---|---|
| Paper step cards | `Web/lib/chapter-pyq/pyqOcrHtml.ts` → `pyqSolutionToHtml` |
| Paper vs glm picker | `Web/lib/mock/ntaQuestionSolution.ts` (`isPaperOcrSolution` → HTML) |
| glm sheet | `Web/components/prep-mock/nta/NtaWorkedSolutionSheet.tsx` |
| Tips / Formula's | `NtaCoachSheet.tsx` + `pyqCoach.ts` (Derivation Path / Formula Codex) |
| Overlay + height | `Web/components/prep-mock/nta/NtaSolutionModal.tsx` |
| glm parse | `Web/lib/chapter-pyq/pyqWorkedSolution.ts` |
| GIF / interval KaTeX | `Web/lib/mock/mockRichTextKatex.ts` → `protectTexBrackets` |
| Tests | `pyqOcrHtml.test.ts`, `pyqWorkedSolution.test.ts`, `mockRichTextKatex.test.ts`, `pyqCoach.test.ts` |
| CSS | `Web/app/globals.css` (`.nta-paper-steps`, `.nta-sol-question`, `.nta-sol-display-box`, `.nta-coach-blueprint`, `.nta-formula-codex`) |

**glm sheet must look like:** Step N + method title, wrapping Question text, boxed **left-aligned** white formulas, trial checks as labeled rows, Final Answer banner.

**glm sheet must behave like:**

- `problem_tex` that is a `\text{If }…` English wall → wrapping inline, never one display.
- Short formula-only `problem_tex` (`I=\int…`) may stay a boxed display.
- Sentences with `$[x]$`, `$[-\pi/2,\pi/2]$` stay **one paragraph**.
- `Testing` / `Check` / `Try $x=…$` → labeled grid rows.
- Long `A=B=C=D` → `stackEqualsChain` (`aligned`), **no horizontal scrollbar** (glm sheet only; paper wavelength **does** scroll a single printed line).
- Sheet hugs content. Cap `max-h-[78dvh]` / `max-h-[min(70vh,38rem)]`. Body `flex-auto min-h-0 overflow-y-auto`, never Tailwind `flex-1`.
- `protectTexBrackets`: `[x]` → `\lbrack … \rbrack`; `[a,b]` → `\left[…\right]`. Never rewrite `\sqrt[3]{…}`.

## JSON the glm solver must emit

`files/agents/solutions.py` `SOLUTION_SYSTEM`:

- `answer` is option `1–4` or the numerical. Must match the official key.
- Steps must **algebraically reach** that key.
- `problem_tex` is the paper stem in LaTeX, no `$`.
- Trial substitutions belong in `grid`.
- One important formula per `display`.

## Hard rules

| Rule | Reality |
|---|---|
| Paper booklet | gemma4 OCR + partition. glm never sees the solution PNG and never overwrites `<!-- paper-ocr -->`. |
| glm sheet | `glm5.3` only. `assert_solution_model`. Never `*-flash`. |
| Tips / Formula's | **After** `solution_md`. glm5.3 JSON from **question + stored solution**. Columns `tips_md` / `formulas_md`. Never a chat paragraph. Never the boxed key. Never coach glm on an empty solution. |
| Vision | `gemma4` for figures / paper crops. Never Gemini. |
| Key | PDF / DB answer is the last **solution** step. Tips stop before that number. |
| Parallel | `max_workers=len(jobs)` for OCR, partition, figure **upload**, glm **solutions**, then a **second** coach pool. Throughput first. Never one-at-a-time in chat. Never mix solution-sheet glm and coach glm in one prompt. |
| Solution figures | **Every** PDF image xref in the crop. Never largest-only. Never a page screenshot. |
| Scope | Only the chapter and year the user named. |
| Students | `review_status in ('auto_ok','human_ok')`. Paper-only stems stay untouched. |

## Paid mistakes — do not regress

| Symptom | Cause | Fix |
|---|---|---|
| Solution looks invented / glm JSON on a booklet that has printed write-ups | Followed the glm sheet path | Follow the paper. gemma4 OCR + partition |
| Two mashed paragraphs, no steps | Paper markdown had no `## Step N` | `layout_math_*_steps.py` — titles only, letters unchanged |
| `Let` / `Zeros in` / `Expression is positive on` stacked above the math | Blind split on every `$` | Join those labels onto the printed line (`shouldJoinPaper`) |
| `By IBP: = ∫…` wrapping through the middle of the integral | Method label glued onto display math | Label **above**; formula `$$` + nowrap (**wavelength**) |
| Shredded `{` brace, `Now \|4x−π/12\| =` sitting below it | Mixed `Now $cases$` stayed **inline**, and/or `.mtable { white-space: normal }` wrapped columns | Display `$$\text{Now }…\begin{cases}$$`; keep mtable **nowrap** |
| `∫ sec^6 θ dθ` then `∫ tan^6 θ + 1 dθ` | OCR split a stacked fraction | One `\frac{num}{den}` inside one `\int`, as printed |
| Popup shows `12. (3)` / `14. (64)` | Copied the listing header | `PAPER_LISTING_PREFIX` / `strip_printed_listing` |
| MathonGo watermark in the popup | Page-crop used as a student figure | Crops are OCR input only; strip `_crop` tokens |
| Page-2 working missing from the popup | Cropped only the first page of a continued write-up | Stitch `continues` onto the next-page band before OCR |
| Diagram missing, or leftover page text in the figure | Page screenshot used as `[[fig:]]`, or no token | PDF image xref `Pixmap(doc, xref)`; never `page.get_pixmap(clip=)` |
| Three printed graphs, popup shows one | `extract_figure` kept only the largest xref | `extract_figures`: every clip xref → `_1` `_2` `_3`; tokens in reading order |
| Piecewise rewritten (`h(x)=0 for 0≤x≤2`) | OCR “simplified” the printed algebra | Copy the printed cases (`x-2+2-x=0`, …). Never drop working. |
| Page-2 last lines gone (`= 3π + 1`) | Crop ended before the last equals | Stitch `continues`; if still short, extend `cut_y` / `clip_y1` |
| Continued-equals line gone (`$=(x-4)x(x-5)$`) | OCR jumped to the sketch | Keep every printed line under the first formula; never drop `$=\\ldots$ |
| Extra broken latex after a “recheck” | Trusted gemma4 missing-line JSON | Revert; only insert what the crop actually shows |
| Popup nested fraction, booklet has two stacked equals (2026 TE Q2) | OCR glued two printed identities; crop gate skipped | Two display lines; open **every** crop vs packet before publish |
| Minus/interval/`\pm`/substitution disagrees with the crop | Trusted OCR JSON or one Q1 screenshot | Walk that crop; publish only crop letters |
| `1 - sin cos x` instead of `1 − 5 cos² x` | Smashed OCR + wrap | Repair from the page; nowrap the working line |
| Students still see the old popup | Forgot the bust | `CHAPTER_PYQ_CACHE_VERSION += 1` |
| Question pill overflows; dark square | glm `problem_tex` as one display | `unwrapProblemTex` / inline mode |
| Stacked empty black formula boxes | Centered `katex-display` + overflow | `text-left`; stack long equals (glm sheet) |
| Popup is only the title + Close | Body `flex-1` | `flex-auto` + max-h hug |
| `[x]` then a broken `[−π/2, π` | Parser split on every `$` | Keep inline math in the sentence |
| Right option, wrong boxed algebra | glm faked the last line | Overwrite; steps must simplify to the key |
| Tips glm with no solution on the row | Coach ran before `solution_md` | Write the paper/glm solution first; then `generate_di_coach.py` |
| Tips is one boring KaTeX paragraph | Hand-wrote coach notes in chat | glm5.3 JSON via `generate_di_coach.py`; Derivation Path cards |
| Last tip states the option / numerical | glm leaked the boxed line | Drop that card; regenerate; validate must reject `\boxed` / `option 1–4` |
| Formula's title shows SQRT3/2 | glm ascii `sqrt` + CSS uppercase | `prettyCoachFormulaName`; name via KaTeX; never ascii sqrt in `name` |
| Formula's shows raw `\begin{aligned}` / `\sum_{k` | `stackEqualsChain` split `{k=1}` as another `=` | Split `=` only outside braces |
| Worked-sheet figure does not enlarge on click | `NtaWorkedSolutionSheet` never called `useNtaFigurePreview` | Same lightbox as stems; `nta-mock-img` click |
| `\rho` in King-rule limits | glm swapped π | Replace with `\pi`; generator `clean_tex` |
| 91 coach rows generated, 0 published | Script returned on two failures | Publish every valid cache; repair the two blobs |
| Tips buttons missing after DB write | Forgot the bust | `CHAPTER_PYQ_CACHE_VERSION += 1` |
| Popup starts with Q1 stem, not the write-up | Cropped the whole Maths session PDF | Crop from `ANSWERS AND SOLUTIONS` / footer `Solutions` only |
| PowerShell ate `$(x-1)` in SQL/markdown | `$()` expanded in a here-string | Write a `.py` file; never embed `$()` in TeX |
| Vercel `Question` vs coach fields | Pushed renderer/types without `npm run build` | `npm run build` in `Web/` before push |
| Step title shows `$\mu$` | Phase `title` was an `<h3>` | `NtaSolutionKatex`; collapse `\\\\mu` |
| Footer chip `1` while working says `= 16` | `polishWorkedSolution` used the MCQ option when the last display duplicated `answer_tex` | Chip the scalar (`16`, `K=1`); keep “Option N is the correct choice” as the note |
| Stem `=14x` / `=724x` | Several equations in one `$…$`; KaTeX drops spaces | `splitGluedLinearEquations` (`,\quad`); repair `$` inners |
| Called C&D complete with 2 holes | Counted contiguous `q_no` and skipped `skeleton_only` / `unreviewed` | Printed PDF count == live `auto_ok\|human_ok`; empty skeleton is a miss |
| Paper OCR `katex_render` hold skipped | Invalid `$` / unpaired braces in packet | Transcribe from the crop; then publish |
| glm sheet says `answer: 3` but the last display is `11/30` or `3/e` | `should_write_solution` checks only the `answer` field, never the working | Read **every step** of every glm sheet before calling it done. Regenerate once; if still wrong, hand-write the phases in the same JSON (`normalize_worked_payload`) |
| glm sheet wanders: "not an integer, recheck", wrong expansion, then "test the options" | glm recovered mid-sheet and kept the dead ends | Rewrite clean; students read the whole sheet |
| KaTeX audit clean but a `tex` cell has `\text{ (reject)` with no `}` | Audit only scanned `$…$` in text fields | Render every `tex`, `displays[]`, `problem_tex`, `answer_tex` string too |
| Tips still show the old wrong route after a rewrite | Coach cache `out-math-pyq-coach/glm/{id}.json` was reused | Delete those cache files, then `generate_pyq_coach.py --overwrite --ids` |
| glm JSON solution treated as paper, figure lost | A leading `[[fig:]]` line before the JSON | Put the figure inside JSON: `{"kind":"figure","html":"<img … class=\"nta-mock-img\">"}` in `phases[].blocks` |

## Red flags — stop

- Saying solutions are done without opening **each** crop PNG against `solution_md`
- Saying glm sheets are done after checking only the `answer` field or the last line
- Nested `\frac{\frac{A}{B}}{\frac{C}{D}}` where the page is two stacked equals
- Solving in this chat one question at a time (always a full parallel pool)
- glm on a booklet that already has printed solutions
- Calling a flash model “because glm5.3 is slow”
- Sending a PNG to `glm5.3`
- Running a chapter the user did not name
- Regenerating glm JSON to fix wrap/alignment (that is parser/UI, or a paper OCR repair)
- Regenerating `solution_md` when the user asked for Tips / Formula's **and solutions already exist**
- Running `generate_di_coach.py` (or writing `tips_md`) before `solution_md` is on the row
- Hand-writing `tips_md` as one paragraph instead of glm JSON moves
- Putting the boxed answer or option number in a tip
- Putting the option index on the FINAL ANSWER chip when the write-up boxed a different number (`16` vs `1`)
- Rendering worked-sheet step titles as plain text
- Saying a chapter’s solutions/stems are done while `skeleton_only` or `unreviewed` rows remain in-scope
- Inventing a type or putting a chapter name on `type`
- Using PDF `get_text` or a vision missing-line dump as the letter check
- Uploading `Downloads\Maths` or a whole session PDF as `solution_md`
- Treating 2026 footer “Questions with Answer Keys” as “no printed write-up”
- Claiming a Web type/renderer change without `npm run build` in `Web/`
