import re

_MCQ = re.compile(r"\b([1-4])\b")


def parse_mcq_choice(text: str) -> int | None:
    m = _MCQ.search(text or "")
    return int(m.group(1)) if m else None


def parse_numerical(text: str) -> str | None:
    t = (text or "").strip()
    return t or None


def solver_has_answer(text: str, key_type: str) -> bool:
    if key_type == "mcq":
        return parse_mcq_choice(text) is not None
    return bool(str(text or "").strip())


def matches_pdf_key(text: str, key_type: str, key_value: str) -> bool:
    key = str(key_value).strip()
    if key_type == "mcq":
        a = parse_mcq_choice(text)
        k = parse_mcq_choice(key)
        return a is not None and a == k
    t = str(text or "").strip()
    return bool(t) and t == key


def solve_match(glm: str, deepseek: str, key_type: str, key_value: str) -> bool:
    """GLM is the gate. DeepSeek only counts when GLM returned nothing."""
    if solver_has_answer(glm, key_type):
        return matches_pdf_key(glm, key_type, key_value)
    if solver_has_answer(deepseek, key_type):
        return matches_pdf_key(deepseek, key_type, key_value)
    return False
