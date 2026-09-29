import unittest

import pyq_common as p


class TestBookConfig(unittest.TestCase):
    def tearDown(self):
        p.configure_book("physics")

    def test_math_points_at_out_math(self):
        spec = p.configure_book("math")
        self.assertTrue(str(p.OUT).replace("\\", "/").endswith("/out-math"))
        self.assertEqual(p.FIGURE_PREFIX, "math/figures")
        self.assertEqual(spec["subject_name"], "Mathematics")

    def test_physics_default(self):
        spec = p.configure_book("physics")
        self.assertTrue(str(p.OUT).replace("\\", "/").endswith("/out"))
        self.assertFalse(str(p.OUT).replace("\\", "/").endswith("/out-math"))
        self.assertEqual(p.FIGURE_PREFIX, "physics/figures")
        self.assertEqual(spec["subject_name"], "Physics")

    def test_unknown_book(self):
        with self.assertRaises(ValueError):
            p.configure_book("chemistry")


if __name__ == "__main__":
    unittest.main()
