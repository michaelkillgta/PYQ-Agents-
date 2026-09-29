#!/usr/bin/env python3
"""Turn Document-AI OCR into paper-only prose with inline $KaTeX$."""
import re

DATE_TAIL = re.compile(
    r"\s*\(?\d{1,2}\s+[A-Za-z]{3,9}\s+20\d{2}\s*\([ME]\)\)?"
)
HEADING_LEAK = re.compile(
    r"\b(?:MUST DO PROBLEMS|CONCEPT BUILDER|ADVANCED(?: STYLE PROBLEMS)?|"
    r"Spring force|Frictional force|Non-uniform Circular Motion|"
    r"Power of iota|Algebra of complex numbers|Geometry of Complex Number|"
    r"Locus Based on Distance Formula|Euler Form and De Moivres Theorem|"
    r"Cube Root of Unity|Conjugate, modulus and argument|Rotation Theorem|"
    r"nth roots of unity|Logarithm|Inequalities|Basic of Mathematics|"
    r"\bAlgebra)\s*$",
    re.I,
)
FIG_LABELS = re.compile(r"\bball\s*\(\s*a\s*\)\s*ball\s*\(\s*b\s*\)", re.I)
PAGE_TAIL = re.compile(r"(?<=\S{3})\s+(?:4[6-9]|5[0-9]|60)\s*$")
HASH_MI = re.compile(r"\s*#\s*#\s*mi\s*$", re.I)
PAGE_FOOTER = re.compile(
    r"(?<=\S)\s+\d{1,3}(?:\s+\d{1,3}){1,4}\s*(?:mi)?\s*$", re.I
)
FIG_TOKEN = re.compile(r"\[\[fig:[^\]]+\]\]")
IMAGE_CAPTION = re.compile(
    r"(?:The image\s+(?:displays|shows|is)\b|"
    r"Note:\s*The function is not explicitly|"
    r"It does not contain any charts|"
    r"The diagram (?:features|illustrates|visually)|"
    r"This image is)\b[\s\S]*",
    re.I,
)
HTML_TABLE = re.compile(r"<table\b[\s\S]*?</table>", re.I)
MD_TABLE = re.compile(r"\|[^\n]*\|[\s\S]*")
MATHONGO = re.compile(
    r"#\s*PaperPhodnaHai|www\.mathongo\.com|\bmathongo\b",
    re.I,
)
MATH_SPLIT = re.compile(r"(\$[^$]*\$)")
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _strip_paper_junk(s: str) -> str:
    """Drop captions, tables, bold markers, watermark. Keep [[fig:KEY]]."""
    figs = FIG_TOKEN.findall(s)
    s = FIG_TOKEN.sub(" ", s)
    s = s.replace("**", "")
    s = DATE_TAIL.sub(" ", s)
    s = HTML_TABLE.sub(" ", s)
    s = IMAGE_CAPTION.sub(" ", s)
    if "|" in s and re.search(r"\|[ \t]*:?-{2,}", s):
        s = MD_TABLE.sub(" ", s)
    s = MATHONGO.sub(" ", s)
    s = FIG_LABELS.sub(" ", s)
    s = HEADING_LEAK.sub(" ", s)
    s = HASH_MI.sub(" ", s)
    s = PAGE_FOOTER.sub(" ", s)
    s = PAGE_TAIL.sub(" ", s)
    s = re.sub(r"[ \t]*\n[ \t]*", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    if figs:
        seen = []
        for f in figs:
            if f not in seen:
                seen.append(f)
        s = f"{s}\n\n" + "\n\n".join(seen)
    return s.strip()


def _map_outside_math(s: str, fn) -> str:
    parts = MATH_SPLIT.split(s)
    out = []
    for part in parts:
        if part.startswith("$") and part.endswith("$") and len(part) >= 2:
            out.append(part)
        else:
            out.append(fn(part))
    return "".join(out)


def _wrap_ocr_chunk(s: str) -> str:
    s = s.replace("⃗", "")
    s = re.sub(r"√\(([^)]+)\)", r"$\\sqrt{\1}$", s)
    s = re.sub(r"√([A-Za-z0-9]+)", r"$\\sqrt{\1}$", s)
    s = re.sub(r"([A-Za-z\\][A-Za-z0-9]*)\^-(\d+)", r"$\1^{-\2}$", s)
    s = re.sub(r"([A-Za-z][A-Za-z0-9]*)\^(\d+)", r"$\1^{\2}$", s)
    s = re.sub(
        r"([A-Za-z])([₀-₉]+)",
        lambda m: f"${m.group(1)}_{{{m.group(2).translate(SUB)}}}$",
        s,
    )
    s = re.sub(r"\b([A-Za-z])\s*=\s*([A-Za-z0-9\\{}^+\-*/]+)", r"$\1 = \2$", s)
    s = re.sub(r"\(\s*([A-Za-z])\s*-\s*([A-Za-z])\s*\)", r"$(\1-\2)$", s)
    s = re.sub(r"(\d+)\s*\^\s*○", r"$\1^{\\circ}$", s)
    s = s.replace("î", r"\hat{i}").replace("ĵ", r"\hat{j}")
    s = re.sub("i\u0302", r"\\hat{i}", s)
    s = re.sub("j\u0302", r"\\hat{j}", s)
    s = re.sub("k\u0302", r"\\hat{k}", s)
    s = re.sub(r"([A-Za-z])²", r"\1^{2}", s)
    s = re.sub(r"([A-Za-z])³", r"\1^{3}", s)
    s = re.sub(
        r"(^|[^$])(\b[A-Za-z]\s*=\s*)(\([^()]*(?:\\hat\{[ijk]\}[^()]*)+\))",
        lambda m: f"{m.group(1)}${m.group(2)}{m.group(3)}$",
        s,
    )
    s = re.sub(r"\s+\*\s*$", "", s)
    return s


def repair_smashed_tex(text: str) -> str:
    """Restore TeX that JSON or unicode OCR ate: int/rac/ext, \\to, \\int, \\lim, GIF \\rbrack."""
    s = text or ""
    s = s.replace("∫", r"\int")
    s = s.replace("∑", r"\sum")
    s = s.replace("∞", r"\infty")
    s = s.replace("→", r"\to")
    tab = "\t"
    s = s.replace(tab + "ext{", r"\text{")
    s = re.sub(tab + r"o(?![A-Za-z])", r"\\to", s)
    s = s.replace(tab + "imes", r"\times")
    s = s.replace(tab + "rac{", r"\frac{")
    s = s.replace(tab + "heta", r"\theta")
    s = re.sub(r"\\{2,}(int|lim)(?![A-Za-z])", lambda m: "\\" + m.group(1), s)
    s = re.sub(r"(^|[^\\a-zA-Z])int([_^])", r"\1\\int\2", s)
    s = re.sub(r"(^|[^\\a-zA-Z])rac\{", r"\1\\frac{", s)
    s = re.sub(r"(^|[^\\a-zA-Z])ext\{", r"\1\\text{", s)
    s = re.sub(r"(^|[^\\a-zA-Z])extinfty", r"\1\\infty", s)
    s = re.sub(r"\)\s*_?o\s*R\b", r") \\to R", s)
    s = re.sub(r"\\text\{\s*\\infty\s*\}", r"\\infty", s)
    s = re.sub(r"\\sqrt\s*\^\s*\{", r"\\sqrt{", s)
    s = re.sub(r"(?<![\\$])√\s*\^\s*\{", r"\\sqrt{", s)
    s = re.sub(r"(?<![\\$])√\s*\{", r"\\sqrt{", s)
    s = re.sub(r"\\sin x \\cdot (\d+)", r"\\sin^{\1} x", s)
    if r"\rbrack" in s and r"\lbrack" not in s:
        s = s.replace(r"\rbrack", "]")
    return s


def format_ocr_math(text: str) -> str:
    s = repair_smashed_tex(text or "")
    s = _strip_paper_junk(s)
    s = re.sub(r"\$\\text\{(_+)\} \$", r"\1", s)
    s = re.sub(r"\$\\text\{(_+)\}\$", r"\1", s)
    s = re.sub(r"\\text\{(_+)\}", r"\1", s)
    s = re.sub(r"\$\$([^$]+)\$\$", r"$\1$", s)
    s = _map_outside_math(s, _wrap_ocr_chunk)
    s = re.sub(r"\$([^$]+)\$\s*-\s*\$([^$]+)\$", r"$\1 - \2$", s)
    s = re.sub(r"\$([^$]+)\$\s*<\s*\$([^$]+)\$", r"$\1 < \2$", s)
    s = re.sub(r"\$([^$]+)\$\s*>\s*\$([^$]+)\$", r"$\1 > \2$", s)
    s = re.sub(r"\$\$+", "$", s)
    s = re.sub(r"\\sqrt\{([^$}]+)\$([^$]+)\$\}", r"$\\sqrt{\1}\2$", s)
    s = re.sub(r"\$\\sqrt\{(\d+)([A-Za-z])\}\$", r"$\\sqrt{\1}\2$", s)
    s = re.sub(r"\$\s+\$", " ", s)
    s = re.sub(r"\$([^$,\s][^$]*)\$\\sqrt\{([^}]+)\}\$", r"$\1\\sqrt{\2}$", s)
    s = _map_outside_math(
        s,
        lambda chunk: re.sub(r"\\sqrt\{([^{}]+)\}", r"$\\sqrt{\1}$", chunk),
    )
    s = re.sub(r"\$\$+", "$", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s
