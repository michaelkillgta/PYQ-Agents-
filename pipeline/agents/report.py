HOLD_REASONS = (
    "coverage_miss",
    "figure_get",
    "vision_conflict",
    "katex_render",
    "solver_mismatch",
    "solver_parse",
    "empty_model",
    "shape",
)


def build_report(chapter_no: int, holds: list) -> str:
    lines = [
        f"# Chapter {chapter_no} verifier report",
        "",
        f"Holds: {len(holds)}",
        "",
    ]
    if not holds:
        lines.append("No holds. Publishable rows are `auto_ok`.")
        lines.append("")
        return "\n".join(lines)

    by_reason: dict[str, list] = {}
    for hold in holds:
        by_reason.setdefault(hold.get("reason") or "unknown", []).append(hold)

    for reason in HOLD_REASONS:
        rows = by_reason.pop(reason, [])
        if not rows:
            continue
        lines.append(f"## {reason}")
        for hold in rows:
            _append_hold_lines(lines, hold, reason)
        lines.append("")

    for reason, rows in sorted(by_reason.items()):
        lines.append(f"## {reason}")
        for hold in rows:
            _append_hold_lines(lines, hold, reason)
        lines.append("")

    lines.append(
        "Fill `decision` on each hold: `keep_key` | `use_glm` | `use_deepseek` | `leave_unreviewed`. "
        "`use_glm` is the default pick; `use_deepseek` is fallback only."
    )
    lines.append(
        f"Then: `python run_chapter_agents.py --chapter {chapter_no} "
        f"--apply-holds out/agents/chapter_{chapter_no}/hold.json`"
    )
    lines.append("")
    return "\n".join(lines)


def _append_hold_lines(lines: list[str], hold: dict, reason: str) -> None:
    q_no = hold.get("q_no")
    if q_no is None:
        lines.append(f"- {hold.get('figure_key') or reason}")
    else:
        lines.append(f"- Q{q_no}")
    if reason == "solver_mismatch":
        lines.append(f"  PDF key: {hold.get('pdf_key')}")
        lines.append(f"  GLM: {hold.get('glm')}")
        lines.append(f"  DeepSeek: {hold.get('deepseek')}")
        preview = hold.get("stem_preview")
        if preview:
            lines.append(f"  stem: {preview}")
    elif reason == "coverage_miss":
        page = hold.get("page")
        if page is not None:
            lines.append(f"  page: {page}")
    elif reason == "figure_get":
        key = hold.get("figure_key")
        if key:
            lines.append(f"  figure_key: {key}")
    detail = hold.get("detail")
    if detail:
        lines.append(f"  {detail}")
