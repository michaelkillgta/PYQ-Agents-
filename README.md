# PYQ Agents

How EduBlast / TestBee turns MathonGo JEE Main PYQ PDFs into the `/chapter-pyq` practice player: the agent skills, the rules, and the Python pipeline. Everything we learned the hard way is written into the skills. Start there.

## What is here

| Path | What it is |
|---|---|
| `.cursor/skills/chapter-pyq/` | Import questions: inventory (no-miss gate), crop, gemma4 OCR, KaTeX gate, publish. Sub-docs: `maths-folder.md` (session PDFs, 29-TOC map), `latex-katex.md`, `new-book.md`. |
| `.cursor/skills/pyq-solutions/` | Worked solutions (paper OCR or glm sheet), then Tips / Formula's coach JSON. Holds the long **Paid mistakes** table. |
| `.cursor/skills/edublast-dev/` | Web / EduDeca / EduBite runbook, git + build + push rules. |
| `.cursor/rules/question-bank-docx-type.mdc` | `type` vs `chapter` vs `class_level` vs difficulty fields. |
| `pipeline/` | Every ingest, solution, coach, audit and repair script (Python), plus `agents/` (models, publish gate, KaTeX check, solution JSON) and `tests/`. |
| `pipeline/PROGRESS.md`, `pipeline/CURSOR_PLAN.md` | Earlier progress log and plan. Older than the skills; the skills win on conflict. |

## Give it to an agent

1. Copy `.cursor/` into the root of the workspace the agent opens (for us: the `EduBlast` folder that holds `Web/`). Cursor loads `.cursor/skills/*/SKILL.md` and `.cursor/rules/*.mdc` automatically.
2. Put `pipeline/` where the scripts expect it. They were written for `C:\Users\tempo\Downloads\files` and read PDFs from `C:\Users\tempo\Downloads\Maths\<Chapter>\`. On another machine, search for `Downloads` and fix the paths first.
3. Create `pipeline/.env` from `.env.example`. Never commit it.
4. `pip install -r pipeline/requirements.txt`. Python 3.14 on Windows, PowerShell, `$env:PYTHONUTF8 = "1"`.
5. KaTeX probes (`katex_probe.mjs`) load KaTeX from `Web/node_modules`; fix that path to your checkout.

Then ask the agent in plain words, e.g. "import the Circle PYQs" or "write solutions for Sequences 2026". The skill descriptions trigger on those.

## The pipeline in one screen

1. **Inventory** — printed `Q n.` count == answer-key count == crop plan, per chapter. Stop on mismatch. (`pyq_ocr_inventory.py`)
2. **Crop + OCR** — one crop per question, gemma4 reads crop + key strip, cached JSON per question, all in parallel. (`ingest_math_named_ocr.py --chapters N` for named Maths chapters)
3. **Publish gate** — shape ok, overlay/caption audit clean (`audit_paper_text.py`), KaTeX renders, not a solver dump → `human_ok`. Else held.
4. **Solutions** — printed write-up exists → follow the paper (gemma4 OCR + step partition). No write-up → glm5.3 JSON sheet (`run_pyq_solutions.py`).
5. **Tips / Formula's** — only after the solution is stored (`generate_pyq_coach.py`).
6. **Bust cache** — `CHAPTER_PYQ_CACHE_VERSION += 1` in `Web/lib/chapter-pyq/cacheVersion.ts`.
7. **Audit** — printed count == live rows, KaTeX on every stem/option/solution field, then look at `/chapter-pyq`.

## Rules that never bend

- Web / TestBee only. Never edit EduDeca or EduBite from this work.
- Models: gemma4 for vision OCR, glm5.3 for solution sheets and coach notes. Never Gemini. glm never sees a PNG.
- The crop PNG is the source of truth, not OCR JSON, not PDF `get_text`.
- Students see `review_status in ('auto_ok','human_ok')` only.
- 2025 Jan/Apr Maths uses that booklet's 29-TOC numbering, never the 33-chapter compilation.
- Never quote extraction accuracy. Never name the page watermark in student-facing text.
- A solution is done only when every step is read, not when its `answer` field matches the key.
- A booklet with no printed key: crop-typed stems, two glm solves, then solve it yourself before publishing. Tell the user the keys are solved, not official.
- Commit or push only when asked. Never force-push. `npm run build` in `Web/` before any push.

## Where the live state is

| Thing | Location |
|---|---|
| Database | Supabase project `bytsiknhtcnlxwzgqkrd`, tables `pyq_subjects`, `pyq_units`, `pyq_chapters`, `pyq_topics`, `pyq_questions`, `pyq_question_options`, `pyq_solutions`, `pyq_figures`, `pyq_figure_links` |
| Figures | Storage bucket `pyq`, prefix `math/figures/` |
| Player code | `testbeeai-ui/TestBee` repo (`Web/`): `lib/chapter-pyq/*`, `components/chapter-pyq/*`, `components/prep-mock/nta/*`, `app/api/chapter-pyq/*` |
| Chapter ↔ PDF map | `Web/lib/chapter-pyq/pdfChapterMap.ts` |

## Not in this repo

- `.env` and any key.
- Source PDFs (`Downloads\Maths`, MathonGo books).
- Output caches (`out-*`: crops, OCR JSON, solve caches). Large and rebuildable; scripts reuse them when present.
- Raw chat transcripts. Their lessons are in the skills; the transcripts themselves are large and may contain keys.
