import re
import subprocess
from pathlib import Path

_GLYPH = re.compile(r"[√²³₁-₉]|[a-zA-Z]\^\d")
_MATH_INNER = re.compile(r"\$([^$]+)\$")
PROBE = Path(__file__).resolve().parent.parent / "katex_probe.mjs"


_NAKED_CMD = re.compile(r"\\(frac|sqrt|in|mathbb|arg|pi)\b")
_MATH_SPLIT = re.compile(r"(\$[^$]*\$)")
_SOLVER_DUMP = re.compile(
    r"the answer is|therefore the absolute value|wait,\s*let me|\\boxed\s*\{|\bcase\s+1\s*:",
    re.I,
)


def dollar_runs_ok(text: str) -> bool:
    return (text or "").count("$") % 2 == 0


def leftover_latex_outside_math(text: str) -> bool:
    for part in _MATH_SPLIT.split(text or ""):
        if part.startswith("$") and part.endswith("$") and len(part) >= 2:
            continue
        if _NAKED_CMD.search(part):
            return True
    return False


def smashed_tex(text: str) -> bool:
    """True when JSON/format ate \\int/\\frac/\\text or doubled \\\\int."""
    s = text or ""
    if re.search(r"(^|[^\\a-zA-Z])int[_^\\]", s):
        return True
    if re.search(r"(^|[^\\a-zA-Z])rac\{", s):
        return True
    if re.search(r"(^|[^\\a-zA-Z])ext(?:\{|infty|log)", s):
        return True
    if re.search(r"\\{2,}(?:int|lim)(?![A-Za-z])", s):
        return True
    if r"\rbrack" in s and r"\lbrack" not in s:
        return True
    if re.search(r"\\sin x \\cdot \d", s):
        return True
    return False


def is_solver_dump(body: str) -> bool:
    s = body or ""
    if _SOLVER_DUMP.search(s):
        return True
    if re.search(r"\bwe need\b", s, re.I) and (
        len(s) > 280 or re.search(r"\b(compute|evaluate|note that|thus|hence)\b", s, re.I)
    ):
        return True
    if re.search(r"\bwe are given\b", s, re.I) and (
        len(s) > 400 or re.search(r"\b(vieta|computing|therefore|hence|thus)\b", s, re.I)
    ):
        return True
    if s.count("\n\n") >= 2 and len(s) > 500 and re.search(
        r"\b(therefore|hence|thus|substituting)\b", s, re.I
    ):
        return True
    return False


def needs_llm_wrap(text: str) -> bool:
    s = text or ""
    if leftover_latex_outside_math(s):
        return True
    if "$" in s:
        return False
    return bool(_GLYPH.search(s))


def probe_tex(tex: str) -> bool:
    r = subprocess.run(
        ["node", str(PROBE), tex],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def katex_render_ok(text: str) -> bool:
    if not dollar_runs_ok(text):
        return False
    if leftover_latex_outside_math(text):
        return False
    if smashed_tex(text):
        return False
    for m in _MATH_INNER.finditer(text or ""):
        if not probe_tex(m.group(1)):
            return False
    return True
