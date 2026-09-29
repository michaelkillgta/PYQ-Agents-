APPLY_DECISIONS = frozenset({
    "keep_key",
    "use_glm",
    "use_deepseek",
    "leave_unreviewed",
})


def apply_hold_decision(hold: dict) -> dict:
    decision = hold.get("decision")
    if decision is None or decision == "leave_unreviewed":
        return {"review_status": "unreviewed", "answer": None, "answer_source": None}
    if decision not in APPLY_DECISIONS:
        raise ValueError(f"unknown hold decision {decision!r}")
    if decision == "keep_key":
        return {
            "review_status": "human_ok",
            "answer": str(hold.get("pdf_key") or "").strip(),
            "answer_source": "pdf_key",
        }
    if decision == "use_glm":
        return {
            "review_status": "human_ok",
            "answer": str(hold.get("glm") or "").strip(),
            "answer_source": "glm",
        }
    if decision == "use_deepseek":
        return {
            "review_status": "human_ok",
            "answer": str(hold.get("deepseek") or "").strip(),
            "answer_source": "deepseek",
        }
    raise ValueError(f"unhandled hold decision {decision!r}")
