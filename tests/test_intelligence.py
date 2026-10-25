import os
import unittest
from unittest.mock import patch

from google.genai.errors import ClientError
from intelligence import (
    AIServiceError,
    _gemini_image_request,
    ask_engineering_assistant,
    calculate_plan,
    demo_crack_report,
    demo_safety_report,
    format_inr,
    weather_advisory,
)


class GeminiConfigurationTests(unittest.TestCase):
    def test_sidebar_key_is_used_instead_of_environment_keys(self):
        with (
            patch.dict(
                os.environ,
                {"GOOGLE_API_KEY": "environment-key", "GEMINI_API_KEY": "another-key"},
            ),
            patch("google.genai.Client") as client_factory,
        ):
            client = client_factory.return_value
            client.models.generate_content.return_value.text = '{"status": "ok"}'

            result = _gemini_image_request(
                "  sidebar-key  ", b"image-bytes", "image/png", "test prompt"
            )

        client_factory.assert_called_once_with(api_key="sidebar-key")
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["model"],
            "gemini-3.8-flash",
        )
        self.assertEqual(result, {"status": "ok"})

    def test_chatbot_uses_the_configured_gemini_model(self):
        with patch("google.genai.Client") as client_factory:
            client_factory.return_value.models.generate_content.return_value.text = "Response"

            response = ask_engineering_assistant(
                "sidebar-key", [{"role": "user", "content": "How should I prepare?"}]
            )

        self.assertEqual(response, "Response")
        self.assertEqual(
            client_factory.return_value.models.generate_content.call_args.kwargs["model"],
            "gemini-3.8-flash",
        )

    def test_missing_sidebar_key_does_not_fall_back_to_environment(self):
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "environment-key"}),
            patch("google.genai.Client") as client_factory,
        ):
            with self.assertRaisesRegex(AIServiceError, "Enter a valid key"):
                _gemini_image_request("", b"image-bytes", "image/png", "test prompt")

        client_factory.assert_not_called()

    def test_invalid_key_error_is_actionable_and_does_not_expose_key(self):
        secret = "private-test-key"
        invalid_key_error = ClientError(
            400,
            {
                "error": {
                    "code": 400,
                    "message": f"API_KEY_INVALID: {secret} is not valid.",
                    "status": "INVALID_ARGUMENT",
                }
            },
        )
        with patch("google.genai.Client") as client_factory:
            client_factory.return_value.models.generate_content.side_effect = invalid_key_error

            with self.assertRaises(AIServiceError) as raised:
                _gemini_image_request(secret, b"image-bytes", "image/png", "test prompt")

        self.assertIn("API_KEY_INVALID", str(raised.exception))
        self.assertIn("dashboard sidebar", str(raised.exception))
        self.assertNotIn(secret, str(raised.exception))


class DemoReportTests(unittest.TestCase):
    def test_safety_demo_does_not_claim_findings(self):
        report = demo_safety_report("site.png")
        self.assertEqual(report["analysis_status"], "not_performed_demo_mode")
        self.assertIsNone(report["safety_score"])
        self.assertEqual(report["site_hazards"], [])
        self.assertTrue(all(item["status"] == "not_assessed" for item in report["ppe_detection"].values()))

    def test_crack_demo_does_not_claim_measurements(self):
        report = demo_crack_report("wall.jpg")
        self.assertEqual(report["analysis_status"], "not_performed_demo_mode")
        self.assertIsNone(report["estimated_crack_width_mm"])
        self.assertEqual(report["root_causes"], [])
        self.assertEqual(report["recommended_repairs"], [])


class PlanningTests(unittest.TestCase):
    def test_calculations_use_only_supplied_values(self):
        result = calculate_plan(1000, 25, 2000, 3000, 4, 0.8)
        self.assertEqual(result["total_budget_inr"], 2_000_000)
        self.assertEqual(result["pro_rata_capex_inr"], 500_000)
        self.assertEqual(result["market_value_inr"], 3_000_000)
        self.assertEqual(result["steel_kg"], 4000)
        self.assertEqual(result["cement_bags"], 800)

    def test_planning_rejects_invalid_completion(self):
        with self.assertRaises(ValueError):
            calculate_plan(100, 101, 0, 0, 0, 0)

    def test_inr_format_uses_lakh_and_crore_units(self):
        self.assertEqual(format_inr(250_000), "₹2.50 L")
        self.assertEqual(format_inr(10_000_000), "₹1.00 Cr")


class AdvisoryTests(unittest.TestCase):
    def test_weather_advisories_are_available(self):
        for condition in ("High Wind", "Heavy Rain", "Extreme Heat", "Normal"):
            title, items = weather_advisory(condition)
            self.assertTrue(title)
            self.assertTrue(items)

    def test_unknown_weather_is_rejected(self):
        with self.assertRaises(ValueError):
            weather_advisory("Monsoon")


if __name__ == "__main__":
    unittest.main()
