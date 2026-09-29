import unittest
from agents.solvers import parse_mcq_choice, solve_match


class TestSolvers(unittest.TestCase):
    def test_parse_option_number(self):
        self.assertEqual(parse_mcq_choice("(2)"), 2)
        self.assertEqual(parse_mcq_choice("2"), 2)
        self.assertEqual(parse_mcq_choice("option 3"), 3)

    def test_glm_matching_key_is_enough(self):
        self.assertTrue(solve_match("2", "2", "mcq", "2"))
        self.assertTrue(solve_match("2", "3", "mcq", "2"))
        self.assertTrue(solve_match("2", "", "mcq", "2"))

    def test_glm_wrong_ignores_deepseek(self):
        self.assertFalse(solve_match("3", "2", "mcq", "2"))
        self.assertFalse(solve_match("3", "3", "mcq", "2"))

    def test_empty_glm_uses_deepseek_fallback(self):
        self.assertTrue(solve_match("", "2", "mcq", "2"))
        self.assertFalse(solve_match("", "3", "mcq", "2"))
        self.assertFalse(solve_match("", "", "mcq", "2"))

    def test_numerical_same_rules(self):
        self.assertTrue(solve_match("12", "99", "numerical", "12"))
        self.assertFalse(solve_match("11", "12", "numerical", "12"))
        self.assertTrue(solve_match("", "12", "numerical", "12"))


if __name__ == "__main__":
    unittest.main()
