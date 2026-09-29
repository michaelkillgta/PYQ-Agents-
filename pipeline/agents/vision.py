def question_rows(payload) -> list:
    if not isinstance(payload, dict):
        return []
    raw = payload.get("questions")
    if not isinstance(raw, list):
        return []
    return [q for q in raw if isinstance(q, dict) and "q_no" in q]


def _index(payload: dict) -> dict:
    out = {}
    for q in question_rows(payload):
        out[int(q["q_no"])] = q
    return out


def vision_agree(parse_page: dict, gemma_page: dict) -> bool:
    a, b = _index(parse_page), _index(gemma_page)
    if set(a) != set(b):
        return False
    for q_no, pq in a.items():
        gq = b[q_no]
        if bool(pq.get("mcq")) != bool(gq.get("mcq")):
            return False
        if int(pq.get("option_count") or 0) != int(gq.get("option_count") or 0):
            return False
    return True


def observer_shape(questions: list, spec_by_q: dict | None = None) -> dict:
    """Document-AI parse → the JSON contract gemma4 / flash must match."""
    rows = []
    for q in questions:
        q_no = int(q["q_no"])
        spec = (spec_by_q or {}).get(q_no) or {}
        opts = q.get("options")
        if isinstance(opts, list):
            mcq, count = True, len(opts)
        elif spec.get("answer_type") == "mcq":
            mcq, count = True, 0
        else:
            mcq, count = False, 0
        rows.append({
            "q_no": q_no,
            "mcq": mcq,
            "option_count": count,
            "has_figure": "[[fig:" in (q.get("body") or ""),
            "body_preview": (q.get("body") or "")[:160],
        })
    return {"questions": rows}
