import unittest
from agents.holds import APPLY_DECISIONS, apply_hold_decision


class TestApplyHolds(unittest.TestCase):
    def test_keep_key_is_human_ok(self):
        out = apply_hold_decision({
            "q_no": 19,
            "reason": "solver_mismatch",
            "pdf_key": "2",
            "glm": "3",
            "deepseek": "2",
            "decision": "keep_key",
        })
        self.assertEqual(out["review_status"], "human_ok")
        self.assertEqual(out["answer"], "2")
        self.assertEqual(out["answer_source"], "pdf_key")

    def test_use_glm(self):
        out = apply_hold_decision({
            "q_no": 19,
            "pdf_key": "2",
            "glm": "3",
            "deepseek": "2",
            "decision": "use_glm",
        })
        self.assertEqual(out["review_status"], "human_ok")
        self.assertEqual(out["answer"], "3")
        self.assertEqual(out["answer_source"], "glm")

    def test_use_deepseek(self):
        out = apply_hold_decision({
            "q_no": 19,
            "pdf_key": "2",
            "glm": "3",
            "deepseek": "2",
            "decision": "use_deepseek",
        })
        self.assertEqual(out["review_status"], "human_ok")
        self.assertEqual(out["answer"], "2")
        self.assertEqual(out["answer_source"], "deepseek")

    def test_leave_unreviewed(self):
        out = apply_hold_decision({
            "q_no": 19,
            "pdf_key": "2",
            "glm": "3",
            "deepseek": "2",
            "decision": "leave_unreviewed",
        })
        self.assertEqual(out["review_status"], "unreviewed")

    def test_null_decision_stays_unreviewed(self):
        out = apply_hold_decision({
            "q_no": 19,
            "pdf_key": "2",
            "glm": "3",
            "deepseek": "2",
            "decision": None,
        })
        self.assertEqual(out["review_status"], "unreviewed")

    def test_unknown_decision_raises(self):
        with self.assertRaises(ValueError):
            apply_hold_decision({"decision": "rewrite_stem"})

    def test_allowed_decisions(self):
        self.assertEqual(
            APPLY_DECISIONS,
            frozenset({"keep_key", "use_glm", "use_deepseek", "leave_unreviewed"}),
        )


if __name__ == "__main__":
    unittest.main()
