"""Worked-solution packets for Chapter PYQ. Text solver is glm5.3 only."""

import json
import re

from agents.models import PRIMARY_SOLVER, VISION_MODEL
from agents.solvers import matches_pdf_key

SOLUTION_MODEL = PRIMARY_SOLVER
VISION_DESCRIBE_MODEL = VISION_MODEL
BANNED_SOLVER_MARKERS = ("flash",)
MIN_SOLUTION_CHARS = 240
SCRATCH = re.compile(r"\b(wait,?|start over|let me redo|scratch)\b", re.I)
PLACEHOLDER = re.compile(r"^[\s.…·•-]*$")


def assert_solution_model(model: str) -> None:
    name = str(model or "").strip()
    if name != SOLUTION_MODEL:
        raise ValueError(f"worked solutions must use {SOLUTION_MODEL}, not {name}")
    if any(marker in name.lower() for marker in BANNED_SOLVER_MARKERS):
        raise ValueError(f"{name} is a flash model and must not write solutions")


def official_key(row: dict) -> tuple[str, str]:
    fmt = str(row.get("format") or "mcq")
    if fmt == "numerical":
        return "numerical", str(row.get("numerical_answer") or "").strip()
    return "mcq", str(row.get("correct_option") or "").strip()


def option_lines(row: dict) -> list[str]:
    opts = row.get("options")
    if not isinstance(opts, list):
        return []
    lines = []
    for i, opt in enumerate(opts, start=1):
        text = str(opt or "").strip()
        if text:
            lines.append(f"({i}) {text}")
    return lines


def combine_question_md(row: dict, figure_md: str = "") -> str:
    parts = ["# Question", str(row.get("body") or "").strip()]
    fig = str(figure_md or "").strip()
    if fig:
        parts.extend(["", "# Figure", fig])
    lines = option_lines(row)
    if lines:
        parts.extend(["", "# Options", *lines])
    _kind, key = official_key(row)
    parts.extend(["", f"Official key: {key}"])
    return "\n".join(parts).strip() + "\n"


def solution_matches_key(answer: str, key_type: str, key_value: str) -> bool:
    if key_type == "numerical":
        got = str(answer or "").strip()
        want = str(key_value).strip()
        if not got or not want:
            return False
        if got == want:
            return True
        try:
            return abs(float(got) - float(want)) < 1e-9
        except ValueError:
            return False
    return matches_pdf_key(answer, "mcq", key_value)


def _str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _callout(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    text = str(raw.get("text") or "").strip()
    tex = str(raw.get("tex") or "").strip()
    if not text and not tex:
        return None
    return {"text": text, "tex": tex}


def _grid(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        tex = str(item.get("tex") or "").strip()
        if label or tex:
            out.append({"label": label, "tex": tex})
    return out


def _block(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind") or "").strip()
    if kind == "paragraph":
        text = str(raw.get("text") or "").strip()
        return {"kind": "paragraph", "text": text} if text else None
    if kind == "callout":
        text = str(raw.get("text") or "").strip()
        tex = str(raw.get("tex") or "").strip()
        if not text and not tex:
            return None
        return {"kind": "callout", "text": text, "tex": tex}
    if kind == "display":
        tex = str(raw.get("tex") or "").strip()
        return {"kind": "display", "tex": tex} if tex else None
    if kind == "grid":
        cells = _grid(raw.get("cells"))
        return {"kind": "grid", "cells": cells} if cells else None
    return None


def _blocks(raw, paragraphs: list[str], callout: dict | None, displays: list[str], grid: list[dict]) -> list[dict]:
    parsed = []
    if isinstance(raw, list):
        for item in raw:
            block = _block(item)
            if block:
                parsed.append(block)
    if parsed:
        return parsed
    blocks = []
    if paragraphs:
        first, *rest = paragraphs
        blocks.append({"kind": "paragraph", "text": first})
    else:
        rest = []
    if callout:
        blocks.append({"kind": "callout", **callout})
    for paragraph in rest:
        blocks.append({"kind": "paragraph", "text": paragraph})
    for tex in displays:
        blocks.append({"kind": "display", "tex": tex})
    if grid:
        blocks.append({"kind": "grid", "cells": grid})
    return blocks


def normalize_worked_payload(data: dict) -> dict | None:
    if not isinstance(data, dict):
        return None
    inner = data.get("solution")
    if isinstance(inner, dict):
        merged = {**inner, "answer": str(data.get("answer") or inner.get("answer") or "").strip()}
        return normalize_worked_payload(merged)
    raw_md = data.get("solution_md")
    if isinstance(raw_md, str) and raw_md.strip().startswith("{"):
        try:
            parsed = json.loads(raw_md)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            parsed = {**parsed, "answer": str(data.get("answer") or parsed.get("answer") or "").strip()}
            return normalize_worked_payload(parsed)
    phases_in = data.get("phases")
    if not isinstance(phases_in, list):
        return None
    phases = []
    for item in phases_in:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        paragraphs = _str_list(item.get("paragraphs"))
        displays = _str_list(item.get("displays"))
        grid = _grid(item.get("grid"))
        callout = _callout(item.get("callout"))
        blocks = _blocks(item.get("blocks"), paragraphs, callout, displays, grid)
        if not paragraphs:
            paragraphs = [b["text"] for b in blocks if b.get("kind") == "paragraph"]
        if not title or not blocks or not paragraphs:
            continue
        phase = {
            "title": title,
            "paragraphs": paragraphs,
            "displays": displays,
            "grid": grid,
            "blocks": blocks,
        }
        if callout:
            phase["callout"] = callout
        phases.append(phase)
    title = str(data.get("title") or "").strip()
    answer = str(data.get("answer") or "").strip()
    if not title or not answer or len(phases) < 2:
        return None
    blob = json.dumps(data, ensure_ascii=False)
    if PLACEHOLDER.match(blob) or SCRATCH.search(blob):
        return None
    return {
        "answer": answer,
        "title": title,
        "problem_tex": str(data.get("problem_tex") or "").strip(),
        "answer_tex": str(data.get("answer_tex") or "").strip(),
        "answer_note": str(data.get("answer_note") or "").strip(),
        "phases": phases,
    }


def dump_worked_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def solution_md_complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw.startswith("{"):
        return False
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False
    return normalize_worked_payload(data) is not None


def should_write_solution(*, answer: str, key_type: str, key_value: str, solution_md: str) -> bool:
    if not solution_md_complete(solution_md):
        return False
    return solution_matches_key(answer, key_type, key_value)


def jobs_for_scope(
    rows: list[dict],
    *,
    year: int | None,
    whole_chapter: bool,
) -> list[dict]:
    if not whole_chapter and year is None:
        raise ValueError("name a year, or pass whole_chapter=True")
    out = []
    for row in rows:
        if not whole_chapter and int(row.get("exam_year") or 0) != int(year):
            continue
        out.append(row)
    return out


def split_solution_paras(text: str) -> list[str]:
    import re

    raw = str(text or "").replace("\r\n", "\n").strip()
    if not raw:
        return []
    chunks = re.split(r"\n{2,}|\n(?=\d+\.\s)", raw)
    return [chunk.replace("\n", " ").strip() for chunk in chunks if chunk.strip()]


SOLUTION_SYSTEM = """You write worked solutions for JEE Main Chapter PYQ.

Audience: Class 11–12 and professionals. Plain English. Short sentences.

Return JSON only with this shape:
{
  "answer": "4",
  "title": "Definite Integral via Symmetry",
  "problem_tex": "I = \\\\int_{-\\\\pi/6}^{\\\\pi/6} \\\\frac{\\\\pi + 4x^{11}}{1 - \\\\sin(|x| + \\\\pi/6)}\\\\,dx",
  "answer_tex": "I = 4\\\\pi",
  "answer_note": "Option 4 is the correct choice",
  "phases": [
    {
      "title": "Symmetry Decomposition",
      "paragraphs": [
        "The denominator $1 - \\\\sin(|x| + \\\\pi/6)$ is an even function since $|-x|=|x|$.",
        "Applying the even-function rule to the remaining part:"
      ],
      "callout": {"text": "Odd component vanishes over $[-a,a]$:", "tex": "\\\\int_{-a}^{a} f_{\\\\text{odd}}(x)\\\\,dx = 0"},
      "displays": ["I = 2\\\\pi \\\\int_{0}^{\\\\pi/6} \\\\frac{dx}{1-\\\\sin(x+\\\\pi/6)}"],
      "grid": [],
      "blocks": [
        {"kind": "paragraph", "text": "The denominator $1 - \\\\sin(|x| + \\\\pi/6)$ is an even function since $|-x|=|x|$."},
        {"kind": "callout", "text": "Odd component vanishes over $[-a,a]$:", "tex": "\\\\int_{-a}^{a} f_{\\\\text{odd}}(x)\\\\,dx = 0"},
        {"kind": "paragraph", "text": "Applying the even-function rule to the remaining part:"},
        {"kind": "display", "tex": "I = 2\\\\pi \\\\int_{0}^{\\\\pi/6} \\\\frac{dx}{1-\\\\sin(x+\\\\pi/6)}"}
      ]
    }
  ]
}

Rules:
- MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units. MUST match Official key.
- title is 3–8 words naming the method.
- problem_tex is the original integral or stem in LaTeX, no $ delimiters.
- 4 to 8 steps. Each title is a verb phrase the student would read in ChatGPT: "Identify the integrand", "Split using even/odd property", "Rationalize the denominator", "Evaluate the antiderivative", "Compute the limits", "Assemble the result".
- Short prose (1–3 sentences). Never a wall of inline integrals. Lengthy write-ups are fine; cramming is not.
- blocks is the reading order. Interleave paragraph, callout, display, and grid. One important formula per display, no $ delimiters.
- callout is optional (theorem / vanishing / King). grid is optional two-column limits/cases: [{"label":"...","tex":"..."}].
- displays are boxed formulas without $ delimiters (the sheet left-aligns them).
- Keep $[x]$ / GIF and $[a,b]$ intervals inside the same English sentence. Do not wrap a full English stem in one \\text{If }… display.
- Trial substitutions (Testing $x=2$ gives …) belong in grid cells, not one prose paragraph.
- The boxed algebra must simplify to Official key. Setting "answer" to the key while the last display is a different expression is wrong.
- answer_tex is the boxed result. answer_note is "Option N is the correct choice" or the numerical value in words.
- Never "...", never draft, never wait, never start over, never **bold**, never mention the model.
"""

VISION_FIGURE_SYSTEM = """Describe this exam figure as markdown for a later text-only solver.

Return JSON only:
{"figure_md":"..."}

Rules:
- Describe axes, curves, shaded regions, labels, and numbers as they appear.
- Use $...$ for math on the figure.
- Do not solve the question. Do not guess missing labels.
"""
