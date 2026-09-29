import json
import unittest

from agents.models import PRIMARY_SOLVER
from agents.solutions import (
    SOLUTION_MODEL,
    VISION_DESCRIBE_MODEL,
    assert_solution_model,
    combine_question_md,
    jobs_for_scope,
    official_key,
    should_write_solution,
    solution_matches_key,
    split_solution_paras,
)


class TestPyqSolutions(unittest.TestCase):
    def test_solver_is_glm53_never_flash(self):
        self.assertEqual(SOLUTION_MODEL, "glm5.3")
        self.assertEqual(SOLUTION_MODEL, PRIMARY_SOLVER)
        self.assertNotIn("flash", SOLUTION_MODEL)
        assert_solution_model("glm5.3")
        for banned in ("glm5.3-flash", "glm5.2-flash", "deepseekv4-flash", "gemma4"):
            with self.assertRaises(ValueError):
                assert_solution_model(banned)

    def test_vision_describe_is_gemma4_not_flash(self):
        self.assertEqual(VISION_DESCRIBE_MODEL, "gemma4")
        self.assertNotIn("flash", VISION_DESCRIBE_MODEL)

    def test_combined_md_has_stem_figure_options_and_key(self):
        md = combine_question_md(
            {
                "format": "mcq",
                "body": "The value of $\\int_0^1 x\\,dx$ is",
                "options": ["$1$", "$1/2$", "$2$", "$0$"],
                "correct_option": 2,
            },
            figure_md="A unit-square sketch with the line $y=x$.",
        )
        self.assertIn("The value of", md)
        self.assertIn("A unit-square sketch", md)
        self.assertIn("(2) $1/2$", md)
        self.assertIn("Official key: 2", md)

    def test_numerical_packet_has_no_fake_options(self):
        md = combine_question_md(
            {
                "format": "numerical",
                "body": "Find $\\int_0^1 2x\\,dx$.",
                "numerical_answer": "1",
            },
            figure_md="",
        )
        self.assertIn("Official key: 1", md)
        self.assertNotIn("(1)", md)

    def test_key_match_mcq_and_numerical(self):
        self.assertTrue(solution_matches_key("2", "mcq", "2"))
        self.assertTrue(solution_matches_key("option 4", "mcq", "4"))
        self.assertFalse(solution_matches_key("3", "mcq", "2"))
        self.assertTrue(solution_matches_key("1", "numerical", "1"))
        self.assertTrue(solution_matches_key("1.0", "numerical", "1"))
        self.assertFalse(solution_matches_key("2", "numerical", "1"))

    def test_never_write_a_mismatched_solution(self):
        long_ok = json.dumps(
            {
                "answer": "2",
                "title": "King's property",
                "problem_tex": "I = \\int_0^{\\pi} \\sin x\\,dx",
                "answer_tex": "I = 2",
                "answer_note": "Option 2 is the correct choice",
                "phases": [
                    {
                        "title": "Setup",
                        "paragraphs": [
                            "Let $I$ be the integral and apply King's property on $[0,\\pi]$."
                        ],
                    },
                    {
                        "title": "Evaluate",
                        "paragraphs": ["Newton-Leibniz on the interval gives $I=2$."],
                        "displays": ["I = 2"],
                    },
                ],
            }
        )
        self.assertFalse(should_write_solution(answer="3", key_type="mcq", key_value="2", solution_md=long_ok))
        self.assertFalse(should_write_solution(answer="2", key_type="mcq", key_value="2", solution_md=""))
        self.assertFalse(should_write_solution(answer="2", key_type="mcq", key_value="2", solution_md="..."))
        self.assertFalse(
            should_write_solution(
                answer="2",
                key_type="mcq",
                key_value="2",
                solution_md="1. wait, start over. 2. This numbered dump is the old format.",
            )
        )
        self.assertTrue(should_write_solution(answer="2", key_type="mcq", key_value="2", solution_md=long_ok))

    def test_keeps_interleaved_blocks_in_reading_order(self):
        from agents.solutions import normalize_worked_payload

        payload = normalize_worked_payload(
            {
                "answer": "4",
                "title": "Definite Integral via Symmetry",
                "problem_tex": "I",
                "answer_tex": "I = 4\\pi",
                "answer_note": "Option 4 is the correct choice",
                "phases": [
                    {
                        "title": "Symmetry Decomposition",
                        "paragraphs": ["Even.", "Apply the even-function rule:"],
                        "callout": {"text": "Odd vanishes", "tex": "0"},
                        "displays": ["I = 2\\pi J"],
                        "blocks": [
                            {"kind": "paragraph", "text": "Even."},
                            {"kind": "callout", "text": "Odd vanishes", "tex": "0"},
                            {"kind": "paragraph", "text": "Apply the even-function rule:"},
                            {"kind": "display", "tex": "I = 2\\pi J"},
                        ],
                    },
                    {
                        "title": "Trigonometric Substitution",
                        "paragraphs": ["Let $J$."],
                    },
                ],
            }
        )
        self.assertIsNotNone(payload)
        self.assertEqual(
            [b["kind"] for b in payload["phases"][0]["blocks"]],
            ["paragraph", "callout", "paragraph", "display"],
        )

    def test_year_scope_keeps_only_that_year(self):
        rows = [
            {"id": "a", "exam_year": 2026, "q_no": 1},
            {"id": "b", "exam_year": 2025, "q_no": 2},
            {"id": "c", "exam_year": 2026, "q_no": 3},
        ]
        year_jobs = jobs_for_scope(rows, year=2026, whole_chapter=False)
        self.assertEqual([j["id"] for j in year_jobs], ["a", "c"])
        all_jobs = jobs_for_scope(rows, year=None, whole_chapter=True)
        self.assertEqual(len(all_jobs), 3)

    def test_one_job_per_question(self):
        rows = [{"id": str(i), "exam_year": 2026, "q_no": i} for i in range(1, 11)]
        jobs = jobs_for_scope(rows, year=2026, whole_chapter=False)
        self.assertEqual(len(jobs), 10)
        self.assertEqual(len({j["id"] for j in jobs}), 10)

    def test_official_key_reads_option_or_numeric(self):
        self.assertEqual(official_key({"format": "mcq", "correct_option": 4}), ("mcq", "4"))
        self.assertEqual(
            official_key({"format": "numerical", "numerical_answer": "12"}),
            ("numerical", "12"),
        )

    def test_split_numbered_steps(self):
        paras = split_solution_paras("Step setup.\n\n1. Use King.\n2. Integrate.")
        self.assertEqual(len(paras), 3)


if __name__ == "__main__":
    unittest.main()
