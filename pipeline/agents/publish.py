from agents.katex_check import is_solver_dump, katex_render_ok
from agents.solvers import parse_mcq_choice
from write_and_publish import options_publishable


def shape_ok_for(spec: dict, entry: dict) -> bool:
    body = (entry.get("body") or "").strip()
    if not body or body.startswith("(OCR missed"):
        return False
    mcq = spec["answer_type"] == "mcq"
    options = entry.get("options")
    if mcq:
        return options_publishable(options)
    return options is None or options == []


def answer_patch(spec: dict, answer: str | None) -> dict:
    if answer is None or answer == "":
        return {}
    if spec["answer_type"] == "mcq":
        choice = parse_mcq_choice(str(answer))
        return {"correct_option": choice} if choice is not None else {}
    return {"numerical_answer": str(answer).strip()}


def upsert_question(sb, question_id: str, entry: dict, status: str,
                    confidence: float, spec: dict, answer: str | None = None) -> None:
    body = (entry.get("body") or "").strip()
    patch = {
        "body": body or None,
        "extraction_confidence": confidence,
        "review_status": status,
    }
    patch.update(answer_patch(spec, answer))
    sb.table("pyq_questions").update(patch).eq("id", question_id).execute()
    options = entry.get("options")
    if options:
        sb.table("pyq_question_options").upsert(
            [
                {"question_id": question_id, "option_index": i, "body": text}
                for i, text in enumerate(options, start=1)
            ],
            on_conflict="question_id,option_index",
        ).execute()


def promote_shape_valid(sb, q_ids: dict, specs: dict, parsed: dict,
                        existing_status: dict) -> tuple[int, int]:
    """Keep auto_ok. Shape-valid holds become human_ok with the PDF key."""
    promoted = 0
    held = 0
    for q_no, spec in specs.items():
        if existing_status.get(q_no) == "auto_ok":
            continue
        entry = parsed.get(str(q_no)) or parsed.get(q_no) or {}
        if not isinstance(entry, dict):
            entry = {}
        if is_solver_dump(entry.get("body") or ""):
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            held += 1
            continue
        fields = [entry.get("body") or ""]
        fields.extend(entry.get("options") or [])
        if not all(katex_render_ok(t) for t in fields):
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            held += 1
            continue
        if shape_ok_for(spec, entry):
            upsert_question(
                sb, q_ids[q_no], entry, "human_ok", 1.0, spec,
                answer=str(spec.get("answer_value") or ""),
            )
            promoted += 1
        else:
            upsert_question(sb, q_ids[q_no], entry, "unreviewed", 0.5, spec)
            held += 1
    return promoted, held
