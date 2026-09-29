def decide_status(gates: dict) -> str:
    if not gates.get("skeleton") or not gates.get("shape_ok") or not gates.get("coverage_ok"):
        return "unreviewed"
    if gates.get("confidence") != 1.0:
        return "flagged"
    for key in ("vision_ok", "figures_ok", "audit_ok", "katex_ok", "solve_match"):
        if not gates.get(key):
            return "flagged"
    return "auto_ok"


def final_publish_status(gates: dict, body: str = "") -> str:
    """Never human_ok a row that fails KaTeX or is a solver dump."""
    from agents.katex_check import is_solver_dump

    if is_solver_dump(body):
        return "unreviewed"
    status = decide_status(gates)
    if status == "auto_ok":
        return "auto_ok"
    if not gates.get("katex_ok"):
        return "unreviewed"
    if gates.get("shape_ok"):
        return "human_ok"
    return status
