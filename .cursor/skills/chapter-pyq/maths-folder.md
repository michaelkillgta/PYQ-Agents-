# Maths source tree (`C:\Users\tempo\Downloads\Maths`)

This folder is the Maths PYQ source. **Do not upload it.** Open the named chapter, split the PDF into questions / keys / solutions, then run chapter-pyq (stems) and pyq-solutions (write-ups). One file is usually all three jobs.

## Layout

| Path | What it is |
|---|---|
| `Maths\Mathematics - JEE Main 2025 January … MathonGo.pdf` | Full **29-TOC** Jan 2025 bank (questions, then answers+solutions). |
| `Maths\Mathematics - JEE Main 2025 April … MathonGo.pdf` | Same for April 2025. |
| `Maths\<Printed title>\YYYY_Jan_….pdf` / `YYYY_Apr_….pdf` | One session booklet for that chapter. |
| `Maths\<Printed title>\2026_….pdf` | January 2026 only (filename has no month). |
| `C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf` | **33-chapter compilation.** Never number 2025 Jan/Apr from this book. |

Typical session files: `2023_Jan`, `2023_Apr`, `2024_Jan`, `2024_Apr`, `2026`. Gaps are real — do not invent a missing month (e.g. Sets and Relations has no `2024_Jan`; Heights has only `2023_Apr`).

Definite Integration also holds 2020–2022 dumps with other filenames. Inventory those separately; do not feed them into a `2024_Jan_` crop plan.

## Same PDF, three sections

Footer lies. 2026 pages still say **Questions with Answer Keys** after the write-ups start. Classify by **heading**, not footer.

| Printed heading / layout | Job | Skill |
|---|---|---|
| `Q1.` / `Q1 - 25 January` / two-column **Space for your notes** | Stems + options | chapter-pyq. Crop **question pages only**. |
| `Answer Key` / compact `Q1 (4)` listing | Official keys | Same inventory. Never OCR this as a stem. |
| `ANSWERS AND SOLUTIONS` or footer **Solutions** (2024+) | Worked write-up | pyq-solutions **Follow the paper**. Crop from this heading to EOF. |

2023 January **Questions with Solutions** books: page 1 is stems with empty text-layer math (ink is drawings) + notes columns; later pages are keys then write-ups. Do not treat page-1 equation pixmaps as student figures.

If the user named a chapter folder and “solutions”, still inventory the split. Uploading the whole PDF as `solution_md` publishes question pages into the popup.

No `ANSWERS AND SOLUTIONS` / `Solutions` section → glm sheet for that year, after stems exist. Do not glm-overwrite a paper packet.

## Catalog (29 TOC) vs leftover folders

`PYQ_MATH_PDF_CHAPTERS` is 1:1 with the 2025 Jan/Apr TOC. Folder name = printed title = catalog slug (slugify).

**Do not source these leftover folders onto a 29-TOC slug:**

| Folder | Why |
|---|---|
| `Limits, Continuity and Differentiability` | Combined 2026 PDF. Catalog leftover slug stays unsourced. Use `Limits\` and `Continuity and Differentiability\` for those two pages. |
| `Differentiation` | Compilation chapter; not in 29 TOC. |
| `Heights and Distances` | Not a catalog chapter. |
| `Mathematical Reasoning` | Compilation only. |
| `Properties of Triangles` | Compilation only. |

Footer may shorten ch.25 to “Trigonometric Ratios”. Still `trigonometric-ratios-and-identities`. Never merge TE into TRI.

## LaTeX — PDF text is not the paper

`page.get_text` on these booklets shreds fractions (`π` then `2` as the next line), drops display math, and leaves option numbers without the formula. **Never publish stems or solutions from the text layer.** Inventory may use footers and `Qn.` listing; letters come from **gemma4 crops**.

After OCR, KaTeX-gate every stem **and option**. Hold smashed `int`/`rac`/`ext`, unpaired `$`, GIF `\rbrack` without `\lbrack`. Details: [latex-katex.md](latex-katex.md).

**Expect these next** (fix from the crop, not from glm):

| Chapter family | Typical OCR/UI failure |
|---|---|
| Trig (TE, TRI, ITF) | Two stacked equals glued into nested `\frac`; `[0,2\pi]` → `(0,2\pi)`; dropped `\pm`; ascii `SQRT3/2` in Formula's names |
| Calculus (Limits → DE, AoD) | Stacked `\frac` split into two `\int`; GIF `[x]` shredded; King `\rho` for `\pi`; `Now` + `cases` brace wrap |
| AUC / conics / 3D / vectors | Graphs as page clips (leftover text); missing xref of three sketches; piecewise rewritten |
| Matrices / determinants | Arrays smashed; `\begin{aligned}` split on `{k=1}` |
| Probability / stats / functions | Cases collapsed; interval commas wrap if `.katex` `white-space: normal` |

Renderer / wrap bugs → Vitest + `pyqOcrHtml.ts` / CSS. Do not glm a new solution.

`npm run build` in `Web/` after any `types/` or NTA popup change. Do not push a type error to Vercel.

## Figures — only real drawings

Maths rasters are uncommon on 2026 question pages (TE 2026: **0** xrefs). AUC / 3D / vectors / 2023 Jan notes pages have many.

| Do | Do not |
|---|---|
| `Pixmap(doc, xref)` for every clip xref that is a graph/sketch | `page.get_pixmap(clip=)` (bakes listing + watermark) |
| Token `[[fig:sYYYYm_slug_qNN_N]]` matching `RASTER_KEY` (`s2025apr_te_q03_1` needs 0–3 month letters) | Keep only the largest xref; skip `_2` `_3` |
| Typeset math beside a sketch stays markdown | Crop Type-3 equation ink / watermark as a figure |
| New storage key when replacing bytes; GET bytes == local | Upsert same key and assume CDN refreshed |
| Tiny graph: enhance PNG. Tiny DI wavy curve may be SVG→raster | Invent SVG for a printed V-tree / axes plot |

Click-to-enlarge is already `NtaFigureLightbox`. Ingest does not add a second popup.

## Exam labels

`2026_Chapter.pdf` → January 2026. `YYYY_Jan_` / `YYYY_Apr_` → that month. Show month + year on year cards. Do not guess 2020 dates from DI dump filenames unless the printed tag is dated.

## Shell

PowerShell. `$env:PYTHONUTF8 = "1"`. Python `C:\Python314\python.exe`. Never embed `$()` in a here-string of `solution_md` (it ate `$(x-1)`). Prefer a `.py` file for SQL/markdown that contains `$`.

## Red flags — stop

- Uploading `Maths\` (or a whole session PDF) as one blob
- `get_text` as the stem or the crop-check
- Cropping question pages into `solution_md`
- Using the LCD combined 2026 file as Limits or C&D
- Numbering from the 33-chapter compilation
- Treating 2026 footer “Answer Keys” as “no printed solutions”
- Page-clip figures; largest-xref-only; Type-3 ink as `[[fig:]]`
- glm sheet on a booklet that has `ANSWERS AND SOLUTIONS`
- Skipping crop-PNG vs packet (nested fraction vs two stacked equals)
- Claiming a Web type/renderer fix without `npm run build`
