import unittest
from agents.coverage import coverage_diff


class TestCoverage(unittest.TestCase):
    def test_ok(self):
        d = coverage_diff({1, 2, 3}, {1, 2, 3})
        self.assertEqual(d["missing"], [])
        self.assertEqual(d["extra"], [])

    def test_miss(self):
        d = coverage_diff({1, 2, 3}, {1, 3})
        self.assertEqual(d["missing"], [2])


if __name__ == "__main__":
    unittest.main()
