"""Sarvam roster for Chapter PYQ ingest.

`glm5.3` is the primary text solver. Other chat models are fallback only —
never a peer vote for auto_ok. Vision models may see page PNGs; text solvers
must not.
"""

VISION_MODEL = "gemma4"
TIEBREAK_MODEL = "glm5.3-flash"
SOLVER_A = "glm5.3"
SOLVER_B = "deepseekv4-flash"
PRIMARY_SOLVER = SOLVER_A
FALLBACK_SOLVERS = (SOLVER_B,)
IMAGE_MODELS = frozenset({VISION_MODEL, TIEBREAK_MODEL})


def assert_model_may_see_image(model: str) -> None:
    if model not in IMAGE_MODELS:
        raise ValueError(f"{model} must not receive a PNG on this Sarvam key")
