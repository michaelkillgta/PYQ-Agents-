import unittest
from agents.katex_check import (
    dollar_runs_ok,
    leftover_latex_outside_math,
    needs_llm_wrap,
    is_solver_dump,
    smashed_tex,
    katex_render_ok,
)


class TestKatexCheck(unittest.TestCase):
    def test_paired_dollars(self):
        self.assertTrue(dollar_runs_ok(r"force $F = ma$ here"))

    def test_odd_dollars_fail(self):
        self.assertFalse(dollar_runs_ok("force $F = ma here"))

    def test_glyph_without_dollar_needs_wrap(self):
        self.assertTrue(needs_llm_wrap("sqrt of x is √x"))
        self.assertFalse(needs_llm_wrap(r"sqrt of x is $\sqrt{x}$"))

    def test_naked_frac_needs_wrap_and_is_leftover(self):
        self.assertTrue(leftover_latex_outside_math(r"\frac{1}{2}"))
        self.assertTrue(needs_llm_wrap(r"\frac{1}{2}"))
        self.assertFalse(leftover_latex_outside_math(r"$\frac{1}{2}$"))

    def test_solver_dump_detected(self):
        self.assertTrue(is_solver_dump("The answer is 13 in a box."))
        self.assertTrue(is_solver_dump(r"Working. The answer is $\boxed{13}$."))
        self.assertFalse(is_solver_dump(r"Let $\alpha$ be a root. Then $n$ equals"))

    def test_smashed_int_frac_text_fail_katex_gate(self):
        self.assertTrue(smashed_tex(r"$int_0^{\pi/4} x\,dx$"))
        self.assertTrue(smashed_tex(r"$(0, ext{\infty})$"))
        self.assertTrue(smashed_tex("$" + r"\\int_{0}^{\pi/4} x dx$"))
        self.assertTrue(smashed_tex("$" + r"\\lim_{n \to \infty} x$"))
        self.assertTrue(smashed_tex(r"$\int_0^1 [-8x^2 \rbrack dx$"))
        self.assertFalse(smashed_tex(r"$\int_0^1 \lbrack -8x^2 \rbrack dx$"))
        self.assertFalse(smashed_tex(r"$\int_0^{\pi/4} x\,dx$"))
        self.assertFalse(katex_render_ok(r"$int_0^{\pi/4} x\,dx$"))
        self.assertTrue(katex_render_ok(r"$\int_0^{\pi/4} x\,dx$"))


if __name__ == "__main__":
    unittest.main()
