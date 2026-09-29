import re
import unittest

from agents.katex_check import katex_render_ok
from format_ocr_math import format_ocr_math


class TestFormatOcrMath(unittest.TestCase):
    def test_keeps_balanced_observer_set_builder(self):
        raw = (
            r"Let $S = \left\{x \in [-6, 3] - \{-2, 2\} : "
            r"\frac{|x+3|-1}{|x|-2} \ge 0\right\}$ and "
            r"$T = \left\{x \in Z : x^2 - 7|x| + 9 \le 0\right\}$. "
            r"Then the number of elements in $S \cap T$ is"
        )
        out = format_ocr_math(raw)
        self.assertIn(r"\left\{x \in [-6, 3]", out)
        self.assertTrue(katex_render_ok(out))
        self.assertEqual(out.count("$") % 2, 0)

    def test_strips_exam_date_and_heading(self):
        raw = r"Then 6a + 5bc is equal to ______. (27 Aug 2021 (M)) Algebra"
        out = format_ocr_math(raw)
        self.assertNotIn("2021", out)
        self.assertNotIn("Algebra", out)
        self.assertIn("______", out)

    def test_keeps_adjacent_sqrt_span(self):
        raw = (
            r"For $\alpha, \beta, z \in \mathbb{C}$ and $\lambda > 1$, "
            r"if $\sqrt{\lambda - 1}$ is the radius of the circle"
        )
        out = format_ocr_math(raw)
        self.assertIn(r"$\sqrt{\lambda - 1}$", out)
        self.assertTrue(katex_render_ok(out))
        self.assertEqual(out.count("$") % 2, 0)

    def test_text_blank_becomes_underscores(self):
        raw = r"The number of solutions of the equation $\log_{4}(x-1) = \log_{2}(x-3)$ is $\text{______}$."
        out = format_ocr_math(raw)
        self.assertIn("______", out)
        self.assertNotIn(r"\text", out)
        self.assertTrue(katex_render_ok(out))

    def test_display_math_before_wrap_keeps_powers(self):
        raw = (
            r"Let $S$ be the sum of the series :"
            r"$$\{x + ka\} + \{x^2 + (k + 2)a\} + \{x^3 + (k + 4)a\}$$"
        )
        out = format_ocr_math(raw)
        self.assertIn(r"\{x^2 + (k + 2)a\}", out)
        self.assertNotIn("{$x^{2}$", out)
        self.assertTrue(katex_render_ok(out))
        raw = (
            r"The sum of the roots of the equation, "
            r"$$x + 1 - 2 \log_2(3 + 2^x) + 2 \log_4(10 - 2^{-x}) = 0$$, is :"
        )
        out = format_ocr_math(raw)
        self.assertNotIn("$$", out)
        self.assertTrue(katex_render_ok(out))
        self.assertIn(r"\log_2", out)

    def test_repairs_json_smashed_text_to_int(self):
        raw = (
            "Let $f, g : (0, "
            + "\t"
            + r"ext{\infty}) "
            + "\t"
            + r"o R$ be two functions defined by $f(x) = "
            + "∫"
            + r"_{-x}^{x} (|t| - t^2) e^{-t^2} dt$ and "
            r"$g(x) = \int_{0}^{x^2} t^{1/2} e^{-t} dt$. "
            r"Then $f(\sqrt^{\text{log}_e 9}) + g(\sqrt{\log_e 9})$."
        )
        out = format_ocr_math(raw)
        self.assertIn(r"\to R", out)
        self.assertIn(r"\infty", out)
        self.assertFalse(re.search(r"(^|[^\\a-zA-Z])ext\{", out))
        self.assertIn(r"\int_{-x}^{x}", out)
        self.assertIn(r"\sqrt{\log_e 9}", out)
        self.assertNotIn(r"\sqrt^", out)
        self.assertTrue(katex_render_ok(out))

    def test_collapses_double_backslash_int(self):
        raw = r"$\int_{0}^{\pi/4} \frac{\cos^2 x \sin^2 x}{(\cos^3 x + \sin^3 x)^2} dx$ is equal to"
        smashed = raw.replace(r"\int", r"\\int", 1)
        out = format_ocr_math(smashed)
        self.assertRegex(out, r"(^|[^\\])\\int_\{0\}")
        self.assertNotRegex(out, r"\\{2,}int(?![A-Za-z])")
        self.assertTrue(katex_render_ok(out))

    def test_sin_cdot_digits_becomes_power(self):
        raw = r"$\frac{1 + \sin^2 x}{1 + e^{\sin x \cdot 2033}}$"
        out = format_ocr_math(raw)
        self.assertIn(r"\sin^{2033} x", out)
        self.assertNotIn(r"\cdot 2033", out)
        self.assertTrue(katex_render_ok(out))

    def test_power_gif_not_collapsed_to_times_floor(self):
        raw = r"The integral $\int_{0}^{1} \dfrac{1}{7^{[1/x]}} dx$"
        out = format_ocr_math(raw)
        self.assertIn(r"7^{[1/x]}", out)
        self.assertNotIn(r"7[1/x]", out)
        self.assertNotIn(r"7 \lfloor", out)
        self.assertTrue(katex_render_ok(out))

    def test_restores_unmatched_gif_rbrack(self):
        raw = r"$\int_{0}^{1} [-8x^{2} + 6x - 1 \rbrack dx$"
        out = format_ocr_math(raw)
        self.assertNotIn(r"\rbrack", out)
        self.assertIn("]", out)
        self.assertTrue(katex_render_ok(out))

    def test_keeps_matched_lbrack_rbrack(self):
        raw = r"$\int_{0}^{1} \lbrack -8x^{2} + 6x - 1 \rbrack \, dx$"
        out = format_ocr_math(raw)
        self.assertIn(r"\lbrack", out)
        self.assertIn(r"\rbrack", out)
        self.assertTrue(katex_render_ok(out))

    def test_repairs_double_backslash_lim(self):
        raw = "$" + r"\\lim_{n \to \infty} x_n$"
        out = format_ocr_math(raw)
        self.assertRegex(out, r"(^|[^\\])\\lim_")
        self.assertNotRegex(out, r"\\{2,}lim")
        self.assertTrue(katex_render_ok(out))

    def test_max_leq_underscript_survives(self):
        raw = (
            r"Let $\operatorname{Max}_{0 \le x \le 2} \left\{\dfrac{9-x^{2}}{5-x}\right\} = \alpha$ "
            r"and $\operatorname{Min}_{0 \le x \le 2} \left\{\dfrac{9-x^{2}}{5-x}\right\} = \beta$"
        )
        out = format_ocr_math(raw)
        self.assertIn(r"0 \le x \le 2", out)
        self.assertNotIn("0<x<", out)
        self.assertTrue(katex_render_ok(out))

    def test_left_hand_limit_minus_survives(self):
        raw = r"Then $\lim_{x \to \left(\dfrac{\pi}{2}\right)^{-}} g(x)$ is equal to"
        out = format_ocr_math(raw)
        self.assertIn(r"^{-}", out)
        self.assertTrue(katex_render_ok(out))


if __name__ == "__main__":
    unittest.main()
