# Chapter PYQ — LaTeX / KaTeX

Students see NTA stems through `useKatexAutoRender`. Raw OCR is not enough: newlines collapse, charts become fake tables, and math without `$…$` stays plain text.

## Pipeline

```
Sarvam digitise JSON
  → parse_ocr_page._keep_block (drop chart/figure/image + markdown tables)
  → format_ocr_math (heuristic $…$)
  → body stored on pyq_questions
  → pyqStemToHtml (wrap prose, keep $…$, resolve [[fig:KEY]])
  → sanitizeMockHtml + patchNtaHtmlPresentation
  → useKatexAutoRender
```

Do not skip a stage. Do not put raw OCR into `questionHtml`.

## Ingestion (`files/format_ocr_math.py`)

After parse, every stem **and every option** runs through `format_ocr_math` (`_strip_paper_junk` first):

- Strip `**`, date tails, overlay OCR (`mathongo`, `# # mi`, `16 4 4 mi`)
- Cut from `The image displays/shows/is…`, `The diagram features/illustrates…`, `Note: The function is not explicitly…`
- Drop `<table>…</table>` and `| :--- |` charts
- Keep `[[fig:KEY]]` (extract, clean, re-append)
- Wrap: `√…`, `^n`, unicode subscripts `t₁` → `$t_{1}$`, `F = kt`, `(p - t)`

The printed paper is: **stem → figure → options**. Captions glued onto option 4 (or option 1) are bugs.

## App (`Web/lib/chapter-pyq/pyqOcrHtml.ts`)

`cleanPyqOcrText` then `pyqStemToHtml`. Options go through `cleanPyqOcrText` in the mapper. Already-balanced `$…$` Maths must stay intact (do not run Physics OCR merge on well-formed spans). Naked `\frac` / `\in` / `\mathbb` on options get `$…$` wrappers. After republish, bump `chapter-pyq-questions-vN` and hard-refresh (API was caching dirty HTML for an hour).

Ingest (`run_chapter_agents.py`): `human_ok` only if every stem and option KaTeX-renders. Odd `$`, leftover `\frac`/`\sqrt`/`\in`/`\mathbb` outside `$…$`, smashed `int`/`rac`/`ext`/`an`/`0` (eaten `\int`/`\frac`/`\text`/`\tan`/`\theta`), or a solver-dump body → hold. `shape_ok` must not override a failed KaTeX probe.

`protectTexBrackets` (`Web/lib/mock/mockRichTextKatex.ts`) runs on every auto-render fragment: GIF `[x]` / `[·]` → `\lbrack … \rbrack`; intervals `[a,b]` → `\left[…\right]`. Never rewrite `\sqrt[3]{…}`. Stems and the Solution popup share this path.

After a published stem changes, regen that row’s `solution_md` (pyq-solutions). Bust `CHAPTER_PYQ_CACHE_VERSION`.

Tests: `Web/lib/chapter-pyq/pyqOcrHtml.test.ts`. Add a case when you change wrapping or caption-stripping.

## What “good” looks like

Q5 Laws of Motion (after fix):

```
The figure represents the momentum time $(p-t)$ curve …
If $(t_{3} - t_{2}) < t_{1}$
[[fig:p047_x550]]
```

Not a markdown table. Not a single smashed line without `$`.

## When math still looks wrong

1. Confirm the stored `body` already has `$…$` (ingestion), not only the CSS.
2. If OCR wrote `t3` instead of `t₃`, extend `format_ocr_math` — do not hand-edit one row unless the user asked for a one-off.
3. Republish the chapter, then hard-refresh (client fetch is once per mount).
4. Never send Gemini a “make this LaTeX” pass unless the user explicitly asks to add a second model.
5. Shredded `[x]` / `[−π/2, π` / missing `/2]` in the **Solution popup** is parser (`protectTexBrackets`, keep `$…$` in one sentence). Do not rewrite the stem unless the DB body is already smashed (`int` / `rac` / `ext`).
6. After a published stem changes, regen that row’s `solution_md` (pyq-solutions), then bump `CHAPTER_PYQ_CACHE_VERSION`.
7. `json.loads` eats `\t` in `\text`/`\to` and rejects `\int`. Salvage TeX backslashes in `parse_json_content` before parse; `repair_smashed_tex` restores `int_`/`rac{`/`ext{`/`\\int`/`\\lim`. Two printed radicals with + are `\sqrt{A}+\sqrt{B}`, never nested. A superscript is `^{n}`, never `\cdot n`. Hold smashed `int`/`rac`/`ext` — KaTeX can still “render” `int_0` as text.
8. 2022 Definite Integration session crops: GIF `\rbrack` without `\lbrack` is a KaTeX error — restore `]` or write a matched `\lbrack...\rbrack` pair (never leave a red `\rbrack`). Left-hand limit is `^{-}`. `7^{[1/x]}` is 7 to the **power** of GIF, never `7[1/x]`. Max/Min underscripts are `0\le x\le 2`, never `0<x<2` (`\operatorname{Max}_{0 \le x \le 2}`, not `\text{Max}_{0<x<2}`). Unpaired `$` after format (`$$$`, missing “such that”, unicode `∞ →` / `ext R`) is a paper override, not a wrap pass.
9. Maths session PDFs (`Downloads\Maths`): **never** take letters from `page.get_text`. OCR glued two stacked equals into one nested `\frac` (2026 TE Q2) — two display lines. Formula's `name` is KaTeX (`prettyCoachFormulaName`), never ascii `SQRT3/2`. Split glm `aligned` only at `=` outside braces. See [maths-folder.md](maths-folder.md).
