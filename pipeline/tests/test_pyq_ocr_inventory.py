import unittest
from pathlib import Path

from pyq_ocr_inventory import (
    COMPACT_KEY_LINE,
    SOL_HEAD_LINE,
    crop_plan,
    inventory_pdf,
    inventory_session_solutions_pdf,
    is_compact_key_page,
    normalize_printed_key,
)

JAN = Path(
    r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"
)
APR = Path(
    r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"
)
SCOPE = ("Definite Integration", "Area Under Curves", "Differential Equations")


class TestCompactKeyPage(unittest.TestCase):
    def test_listing_is_key_page(self):
        text = "Indefinite Integration\n1. (2)\n2. (16)\nDefinite Integration\n1. (4)\n"
        self.assertTrue(is_compact_key_page(text))

    def test_worked_solution_is_not_key_page(self):
        text = "Q1.\n(1)\nBasic of Mathematics\nJEE Main 2025 January\n1. (4)\n"
        self.assertFalse(is_compact_key_page(text))

    def test_toc_is_not_key_page(self):
        text = "Content\nAnswer Keys\nDefinite Integration\n37\n"
        self.assertFalse(is_compact_key_page(text))


@unittest.skipUnless(JAN.is_file() and APR.is_file(), "2025 chapter-wise PDFs not on disk")
class TestPyqOcrInventory(unittest.TestCase):
    def test_january_di_auc_de_matches_answer_keys(self):
        report = inventory_pdf(JAN, list(SCOPE))
        by_title = {c["title"]: c for c in report["chapters"]}
        self.assertTrue(report["gate_ok"], format_fail(report))
        self.assertEqual(report["key_pages"], [67, 68])
        self.assertEqual(by_title["Definite Integration"]["printed_count"], 13)
        self.assertEqual(by_title["Area Under Curves"]["printed_count"], 12)
        self.assertEqual(by_title["Differential Equations"]["printed_count"], 12)
        self.assertEqual(report["printed_total"], 37)
        self.assertEqual(report["crop_total"], 37)
        self.assertEqual(report["key_total"], 37)

    def test_january_follows_toc_chapter_titles_not_compilation_book(self):
        from pyq_ocr_inventory import MATH_CHAPTER_TITLES

        self.assertNotIn("Differentiation", MATH_CHAPTER_TITLES)
        self.assertNotIn("Mathematical Reasoning", MATH_CHAPTER_TITLES)
        self.assertEqual(len(MATH_CHAPTER_TITLES), 29)
        report = inventory_pdf(JAN, list(MATH_CHAPTER_TITLES))
        by_title = {c["title"]: c for c in report["chapters"]}
        self.assertTrue(report["gate_ok"], format_fail(report))
        self.assertEqual(report["printed_total"], 250)
        self.assertEqual(by_title["Trigonometric Ratios & Identities"]["printed_count"], 4)
        self.assertEqual(by_title["Continuity and Differentiability"]["printed_count"], 6)
        self.assertEqual(by_title["Continuity and Differentiability"]["key_count"], 6)

    def test_april_di_auc_de_matches_answer_keys(self):
        report = inventory_pdf(APR, list(SCOPE))
        by_title = {c["title"]: c for c in report["chapters"]}
        self.assertTrue(report["gate_ok"], format_fail(report))
        self.assertEqual(report["key_pages"], [64, 65])
        self.assertEqual(by_title["Definite Integration"]["printed_count"], 9)
        self.assertEqual(by_title["Area Under Curves"]["printed_count"], 7)
        self.assertEqual(by_title["Differential Equations"]["printed_count"], 10)
        self.assertEqual(report["printed_total"], 26)
        self.assertEqual(report["crop_total"], 26)
        self.assertEqual(report["key_total"], 26)

    def test_titles_are_found_on_full_page_not_header_only(self):
        report = inventory_pdf(JAN, ["Area Under Curves"])
        auc = report["chapters"][0]
        self.assertEqual(auc["pages"], [40, 41, 42])
        self.assertEqual(auc["printed"], list(range(1, 13)))
        self.assertTrue(auc["gate_ok"])
        self.assertEqual(auc["crop_count"], 12)

    def test_crop_plan_stitches_same_title_continuation(self):
        report = inventory_pdf(JAN, ["Definite Integration"])
        di = report["chapters"][0]
        plan = crop_plan(di)
        self.assertEqual(len(plan), 13)
        continued = [s for s in plan if s["continues"]]
        self.assertTrue(continued, "at least one DI question continues onto the next DI page")
        self.assertTrue(all(s["continuation"]["page"] in di["pages"] for s in continued))


SESSION_BOOKS = {
    "2021-feb": (
        Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_february_chapterwiseW7xhGEpjPf0BnZlSz5TE.pdf"),
        14,
    ),
    "2021-mar": (
        Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_march_chapterwise_JhLuivAhhuEbSCISHMto.pdf"),
        9,
    ),
    "2022-jun": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2022 Chapter wise Questions by MathonGo.pdf"),
        20,
    ),
    "2022-jul": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration.pdf"),
        20,
    ),
    "2023-jan": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 January Chapter wise Questions by MathonGo.pdf"),
        24,
    ),
    "2023-apr": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 April Chapterwise PYQ - MathonGo.pdf"),
        13,
    ),
    "2024-jan": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
        20,
    ),
    "2024-apr": (
        Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
        14,
    ),
}


@unittest.skipUnless(all(p.is_file() for p, _n in SESSION_BOOKS.values()), "session DI PDFs not on disk")
class TestSessionDiInventory(unittest.TestCase):
    def test_every_session_book_printed_matches_answer_key(self):
        from pyq_ocr_inventory import inventory_session_pdf

        for bid, (pdf, expect) in SESSION_BOOKS.items():
            with self.subTest(bid):
                report = inventory_session_pdf(pdf)
                self.assertTrue(report["gate_ok"], f"{bid} {format_fail(report)}")
                self.assertEqual(report["printed_total"], expect, bid)
                self.assertEqual(report["key_total"], expect, bid)
                self.assertEqual(report["crop_total"], expect, bid)
                self.assertNotIn("Hints and Solutions", " ".join(
                    str(p) for p in report["chapters"][0]["pages"]
                ))


JAN_2026_DI = Path(
    r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf"
)
JAN_2026_KEYS = {
    1: "9",
    2: "2",
    3: "3",
    4: "2",
    5: "2",
    6: "36",
    7: "3",
    8: "16",
    9: "4",
    10: "17",
    11: "4",
    12: "3",
    13: "210",
    14: "64",
}


class TestCompactVsSolutionHeadings(unittest.TestCase):
    def test_compact_strip_is_not_a_writeup(self):
        self.assertTrue(COMPACT_KEY_LINE.fullmatch("1. 9"))
        self.assertTrue(COMPACT_KEY_LINE.fullmatch("2. (2)"))
        self.assertTrue(COMPACT_KEY_LINE.fullmatch("13. 210"))
        self.assertFalse(COMPACT_KEY_LINE.fullmatch("1. (9) Let"))
        self.assertFalse(COMPACT_KEY_LINE.fullmatch("4. (2) Given:"))

    def test_solution_heading_keeps_the_boxed_key(self):
        self.assertTrue(SOL_HEAD_LINE.match("1. (9) Let"))
        self.assertTrue(SOL_HEAD_LINE.match("3. (3)"))
        self.assertTrue(SOL_HEAD_LINE.match("6. (36)"))
        self.assertEqual(SOL_HEAD_LINE.match("14. (64) From").group(2), "64")


@unittest.skipUnless(JAN_2026_DI.is_file(), "2026 January DI PDF not on disk")
class TestJan2026PrintedSolutionsInventory(unittest.TestCase):
    def test_questions_keys_solutions_are_14(self):
        report = inventory_session_solutions_pdf(JAN_2026_DI)
        self.assertTrue(report["gate_ok"], format_fail(report))
        self.assertEqual(report["printed_total"], 14)
        self.assertEqual(report["key_total"], 14)
        self.assertEqual(report["solution_total"], 14)
        self.assertEqual(report["crop_total"], 14)
        chapter = report["chapters"][0]
        self.assertEqual(chapter["printed"], list(range(1, 15)))
        self.assertEqual(chapter["solutions"], list(range(1, 15)))
        got = {n: normalize_printed_key(v) for n, v in chapter["keys"].items()}
        self.assertEqual(got, JAN_2026_KEYS)
        continued = [s for s in chapter["crop_plan"] if s["continues"]]
        self.assertTrue(continued, "at least one 2026 solution stitches onto the next page")
        self.assertTrue(all(s["continuation"]["page"] in chapter["pages"] for s in continued))


@unittest.skipUnless(
    SESSION_BOOKS["2024-jan"][0].is_file() and SESSION_BOOKS["2024-apr"][0].is_file(),
    "2024 DI question-bank PDFs not on disk",
)
class Test2024QuestionBankSolutionsInventory(unittest.TestCase):
    def test_jan_and_apr_solution_writeups_match_keys(self):
        from pyq_ocr_inventory import inventory_session_questionbank_solutions

        expect = {"2024-jan": 20, "2024-apr": 14}
        for bid, n in expect.items():
            pdf = SESSION_BOOKS[bid][0]
            with self.subTest(bid):
                report = inventory_session_questionbank_solutions(pdf)
                self.assertTrue(report["gate_ok"], format_fail(report))
                self.assertEqual(report["printed_total"], n, bid)
                self.assertEqual(report["key_total"], n, bid)
                self.assertEqual(report["solution_total"], n, bid)
                self.assertEqual(report["crop_total"], n, bid)
                self.assertEqual(report["chapters"][0]["printed"], list(range(1, n + 1)))
                self.assertEqual(report["style"], "questionbank-solutions")


def format_fail(report: dict) -> str:
    bits = [f"gate_ok={report['gate_ok']} key_pages={report.get('key_pages')}"]
    for c in report["chapters"]:
        bits.append(
            f"{c['title']} printed={c['printed_count']} keys={c['key_count']} crops={c['crop_count']}"
        )
    return "; ".join(bits)


if __name__ == "__main__":
    unittest.main()
