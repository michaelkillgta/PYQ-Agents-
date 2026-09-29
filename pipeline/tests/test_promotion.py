import unittest
from agents.promotion import decide_status, final_publish_status

BASE = {
    "skeleton": True,
    "shape_ok": True,
    "coverage_ok": True,
    "vision_ok": True,
    "figures_ok": True,
    "audit_ok": True,
    "katex_ok": True,
    "solve_match": True,
    "confidence": 1.0,
}


class TestDecideStatus(unittest.TestCase):
    def test_all_gates_auto_ok(self):
        self.assertEqual(decide_status(BASE), "auto_ok")

    def test_single_observer_never_auto_ok(self):
        g = {**BASE, "confidence": 0.5}
        self.assertNotEqual(decide_status(g), "auto_ok")

    def test_solver_mismatch_flagged(self):
        g = {**BASE, "solve_match": False}
        self.assertEqual(decide_status(g), "flagged")

    def test_shape_fail_unreviewed(self):
        g = {**BASE, "shape_ok": False}
        self.assertEqual(decide_status(g), "unreviewed")

    def test_human_ok_requires_katex(self):
        g = {**BASE, "katex_ok": False, "solve_match": False, "confidence": 0.5}
        self.assertEqual(final_publish_status(g, r"Let $z$ be complex"), "unreviewed")

    def test_solver_dump_never_publishes(self):
        self.assertEqual(
            final_publish_status(BASE, "The answer is 13 after we compute alpha."),
            "unreviewed",
        )

    def test_shape_ok_still_human_ok_when_katex_passes(self):
        g = {**BASE, "solve_match": False, "confidence": 0.5}
        self.assertEqual(final_publish_status(g, r"Let $z$ be complex"), "human_ok")


if __name__ == "__main__":
    unittest.main()
