#!/usr/bin/env python3
"""Split a Sarvam Document AI page into skeleton-aligned questions.

No chat model. q_no and figure_keys come from the immutable skeleton.
"""
import re

from format_ocr_math import format_ocr_math

Q_HEAD = re.compile(
    r"(?:^|\n)\s*\*{0,2}Q\s*(\d+)\s*(?:\^)?[.•*·]?\*{0,2}\s*",
    re.I,
)
OPT_SPLIT = re.compile(r"\n?\s*\(([1-4])\)\s*")
DATE_TAIL = re.compile(
    r"\s*\d{1,2}\s+[A-Za-z]{3,9}\s+20\d{2}\s*\([ME]\)\s*"
)
HEADING_LINE = re.compile(
    r"^(must do problems|concept builder|advanced(?: style problems)?|"
    r"mechanics \d+|laws of motion|newton.?s laws of motion|friction|"
    r"equilibrium of forces|circular motion|non-uniform circular motion|"
    r"spring force|frictional force|"
    r"quadratic equation|relation between roots and coefficients|"
    r"graph and sign of quadratic|range of quadratic function|"
    r"common roots|location of roots|n degree equation)$",
    re.I,
)


SKIP_TAGS = {"chart", "figure", "image"}
SKIP_TEXT = (
    "the image displays",
    "the image shows",
    "the image is",
    "the image is not",
    "note: the function is not explicitly",
    "it does not contain any charts",
    "the diagram features",
    "the diagram illustrates",
    "this image is",
)


def _keep_block(tag: str, text: str) -> bool:
    if (tag or "").lower() in SKIP_TAGS:
        return False
    low = text.lower().lstrip("*").strip()
    if any(low.startswith(p) for p in SKIP_TEXT):
        return False
    if "| :---" in text or low.startswith("| label |") or "<table" in low:
        return False
    return True


def _blocks_in_order(payload: dict) -> list[str]:
    docs = payload.get("documents") or []
    texts = []
    for doc in docs:
        for page in doc.get("pages") or []:
            blocks = sorted(page.get("blocks") or [],
                            key=lambda b: b.get("reading_order") or 0)
            for b in blocks:
                t = (b.get("text") or "").strip()
                if t and _keep_block(b.get("layout_tag") or "", t):
                    texts.append(t)
    return texts


def _split_options(blob: str) -> list[str] | None:
    parts = OPT_SPLIT.split(blob)
    if len(parts) < 3:
        return None
    # parts: [preamble, '1', opt1, '2', opt2, ...]
    by_idx = {}
    i = 1
    while i + 1 < len(parts):
        try:
            n = int(parts[i])
        except ValueError:
            i += 2
            continue
        by_idx[n] = parts[i + 1].strip()
        i += 2
    if set(by_idx) >= {1, 2, 3, 4}:
        return [DATE_TAIL.sub("", by_idx[n]).strip() for n in (1, 2, 3, 4)]
    return None


def parse_digitise_to_questions(payload: dict, slice_: list[dict]) -> list[dict]:
    """Return one record per skeleton q_no on this page."""
    wanted = {s["q_no"]: s for s in slice_}
    texts = _blocks_in_order(payload)
    joined = "\n\n".join(texts)

    chunks = {}
    matches = list(Q_HEAD.finditer(joined))
    for i, m in enumerate(matches):
        q_no = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(joined)
        chunks[q_no] = joined[start:end].strip()

    questions = []
    for q_no, spec in wanted.items():
        raw = chunks.get(q_no, "")
        raw = DATE_TAIL.sub("", raw)
        raw = "\n".join(
            ln for ln in raw.splitlines() if not HEADING_LINE.match(ln.strip())
        ).strip()
        options = _split_options(raw) if spec["answer_type"] == "mcq" else None
        if options:
            body = OPT_SPLIT.split(raw)[0].strip()
            options = [format_ocr_math(o) for o in options]
        else:
            body = raw
            if spec["answer_type"] == "mcq":
                options = None  # whitelist shape check happens later
        body = format_ocr_math(body)
        for key in spec["figure_keys"]:
            token = f"[[fig:{key}]]"
            if token not in body:
                body = f"{body}\n\n{token}".strip()
        questions.append({
            "q_no": q_no,
            "body": body or f"(OCR missed stem for Q{q_no})",
            "options": options if spec["answer_type"] == "mcq" else None,
        })
    return questions
