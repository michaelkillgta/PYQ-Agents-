import unittest
from agents.figures_check import missing_figure_gets


class TestFiguresCheck(unittest.TestCase):
    def test_reports_non_200(self):
        def fake_get(url: str) -> int:
            return 200 if "ok" in url else 404
        missing = missing_figure_gets(
            {"a": "https://x/ok.png", "b": "https://x/bad.png"},
            get_status=fake_get,
        )
        self.assertEqual(missing, ["b"])


if __name__ == "__main__":
    unittest.main()
