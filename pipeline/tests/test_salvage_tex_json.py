import json
import unittest

from pyq_common import salvage_tex_json


class TestSalvageTexJson(unittest.TestCase):
    def test_text_and_to_are_not_eaten_as_tab(self):
        model = r'{"body": "Let $f, g : (0, \text{\infty}) \to R$"}'
        parsed = json.loads(salvage_tex_json(model))
        self.assertIn(r"\text", parsed["body"])
        self.assertIn(r"\to", parsed["body"])
        self.assertNotIn("\t", parsed["body"])

    def test_int_is_valid_json_and_stays_one_slash(self):
        model = r'{"body": "$\int_0^1 x dx$"}'
        parsed = json.loads(salvage_tex_json(model))
        self.assertEqual(parsed["body"], r"$\int_0^1 x dx$")

    def test_already_escaped_int_is_not_tripled(self):
        model = '{"body": "$\\\\int_0^1 x dx$"}'
        parsed = json.loads(salvage_tex_json(model))
        self.assertEqual(parsed["body"], r"$\int_0^1 x dx$")


if __name__ == "__main__":
    unittest.main()
