import unittest
from agents.report import build_report


class TestReport(unittest.TestCase):
    def test_lists_solver_hold(self):
        text = build_report(5, [{"q_no": 19, "reason": "solver_mismatch",
                                 "pdf_key": "2", "glm": "3", "deepseek": "2"}])
        self.assertIn("19", text)
        self.assertIn("solver_mismatch", text)
        self.assertIn("PDF key", text)


if __name__ == "__main__":
    unittest.main()
