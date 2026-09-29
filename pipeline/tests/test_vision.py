import unittest
from agents.vision import vision_agree


class TestVision(unittest.TestCase):
    def test_same_q_set_and_shape(self):
        parse = {"questions": [{"q_no": 1, "mcq": True, "option_count": 4}]}
        gemma = {"questions": [{"q_no": 1, "mcq": True, "option_count": 4}]}
        self.assertTrue(vision_agree(parse, gemma))

    def test_missing_q(self):
        parse = {"questions": [{"q_no": 1, "mcq": True, "option_count": 4}]}
        gemma = {"questions": []}
        self.assertFalse(vision_agree(parse, gemma))

    def test_questions_string_is_not_agree(self):
        parse = {"questions": [{"q_no": 1, "mcq": True, "option_count": 4}]}
        gemma = {"questions": "unterminated json junk"}
        self.assertFalse(vision_agree(parse, gemma))


if __name__ == "__main__":
    unittest.main()
