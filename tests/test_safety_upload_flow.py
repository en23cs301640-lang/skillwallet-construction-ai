from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

import intelligence


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(80, 120, 160)).save(buffer, format="PNG")
    return buffer.getvalue()


def safety_dashboard() -> AppTest:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    test_app = AppTest.from_file(app_path).run()
    test_app.query_params["view"] = "dashboard"
    test_app.query_params["feature"] = "safety"
    return test_app.run()


class SafetyUploadFlowTests(unittest.TestCase):
    def test_analyze_button_passes_uploaded_image_and_shows_result(self):
        image = png_bytes()
        report = {
            "analysis_status": "ai_generated_preliminary",
            "source_file": "site.png",
            "safety_score": 77,
            "overall_status": "Potential concerns",
            "ppe_detection": {
                name: {"status": "unclear", "evidence": "Test fixture only"}
                for name in ("helmet", "high_visibility_vest", "steel_toe_boots", "safety_harness")
            },
            "site_hazards": [],
        }

        with patch.object(intelligence, "analyze_safety_image", return_value=report) as analyze:
            test_app = safety_dashboard()
            test_app.file_uploader(key="safety_image").set_value(
                ("site.png", image, "image/png")
            )
            test_app.text_input(key="gemini_api_key").set_value("test-key-not-real")
            test_app.run()
            test_app.button(key="analyze_safety").click().run()

        analyze.assert_called_once()
        self.assertEqual(analyze.call_args.args[1:], (image, "image/png", "site.png"))
        self.assertIn("77 / 100", [metric.value for metric in test_app.metric])
        self.assertFalse(test_app.exception)
        self.assertFalse(test_app.error)

    def test_missing_api_key_shows_actionable_error_without_demo_report(self):
        test_app = safety_dashboard()
        test_app.file_uploader(key="safety_image").set_value(
            ("site.png", png_bytes(), "image/png")
        )
        test_app.run()
        test_app.button(key="analyze_safety").click().run()

        self.assertTrue(
            any("Gemini API key required" in error.value for error in test_app.error)
        )
        self.assertNotIn("safety_report", test_app.session_state)
        self.assertFalse(test_app.exception)

    def test_unreadable_upload_is_reported_before_preview_or_analysis(self):
        test_app = safety_dashboard()
        test_app.file_uploader(key="safety_image").set_value(
            ("not-an-image.png", b"not image bytes", "image/png")
        )
        test_app.run()

        self.assertTrue(
            any("not a readable image" in error.value for error in test_app.error)
        )
        self.assertTrue(test_app.button(key="analyze_safety").disabled)
        self.assertFalse(test_app.exception)

    def test_gemini_error_is_visible_and_does_not_create_a_report(self):
        with patch.object(
            intelligence,
            "analyze_safety_image",
            side_effect=intelligence.AIServiceError("Gemini image analysis failed: invalid key"),
        ):
            test_app = safety_dashboard()
            test_app.file_uploader(key="safety_image").set_value(
                ("site.png", png_bytes(), "image/png")
            )
            test_app.text_input(key="gemini_api_key").set_value("test-key-not-real")
            test_app.run()
            test_app.button(key="analyze_safety").click().run()

        self.assertTrue(
            any("invalid key" in error.value for error in test_app.error)
        )
        self.assertNotIn("safety_report", test_app.session_state)
        self.assertFalse(test_app.exception)


if __name__ == "__main__":
    unittest.main()
