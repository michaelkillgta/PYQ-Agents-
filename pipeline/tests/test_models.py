import unittest
from agents.models import (
    FALLBACK_SOLVERS,
    IMAGE_MODELS,
    PRIMARY_SOLVER,
    assert_model_may_see_image,
)
from pyq_common import RateLimiter, call_sarvam_v2


class TestImageAllowList(unittest.TestCase):
    def test_glm_is_primary_text_solver(self):
        self.assertEqual(PRIMARY_SOLVER, "glm5.3")
        self.assertEqual(FALLBACK_SOLVERS, ("deepseekv4-flash",))

    def test_gemma4_and_flash_may_see_png(self):
        assert_model_may_see_image("gemma4")
        assert_model_may_see_image("glm5.3-flash")

    def test_text_solvers_must_not_see_png(self):
        for model in ("glm5.3", "deepseekv4-flash", "glm5.2", "sarvam-105b"):
            with self.assertRaises(ValueError):
                assert_model_may_see_image(model)

    def test_image_models_frozen(self):
        self.assertEqual(IMAGE_MODELS, frozenset({"gemma4", "glm5.3-flash"}))

    def test_v2_rejects_png_before_http(self):
        messages = [{
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,xx"}}],
        }]
        with self.assertRaises(ValueError):
            call_sarvam_v2("glm5.3", messages, "dummy-key", RateLimiter())
        with self.assertRaises(ValueError):
            call_sarvam_v2("deepseekv4-flash", messages, "dummy-key", RateLimiter())


if __name__ == "__main__":
    unittest.main()
