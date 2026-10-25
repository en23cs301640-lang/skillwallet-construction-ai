"""AI integration and calculation helpers for the construction intelligence app."""

from __future__ import annotations

import json
import re
from typing import Any

GEMINI_MODEL = "gemini-3.8-flash"


class AIServiceError(RuntimeError):
    """Raised when an AI request or its response cannot be safely completed."""


def _create_gemini_client(api_key: str) -> Any:
    """Use only the key supplied by the active Streamlit session."""
    key = api_key.strip()
    if not key:
        raise AIServiceError(
            "Gemini API key required. Enter a valid key in the dashboard sidebar."
        )

    from google import genai

    return genai.Client(api_key=key)


def _gemini_request_error(exc: Exception, api_key: str, operation: str) -> AIServiceError:
    details = str(exc)
    normalized_key = api_key.strip()
    if normalized_key:
        details = details.replace(normalized_key, "[redacted]")
    normalized_details = details.casefold()
    if "api_key_invalid" in normalized_details or (
        "api key" in normalized_details
        and ("not valid" in normalized_details or "invalid" in normalized_details)
    ):
        return AIServiceError(
            "Google rejected the Gemini API key (API_KEY_INVALID). Replace it with a valid "
            "Gemini API key in the dashboard sidebar, then submit the request again. "
            "No analysis was completed."
        )
    return AIServiceError(f"Gemini {operation} failed: {details}")


def demo_safety_report(filename: str) -> dict[str, Any]:
    """Return an explicit, empty demo report without inferring image contents."""
    return {
        "analysis_status": "not_performed_demo_mode",
        "source_file": filename,
        "notice": "No image analysis was performed. Supply a Gemini API key to request AI analysis.",
        "safety_score": None,
        "overall_status": "Not assessed",
        "ppe_detection": {
            item: {"status": "not_assessed", "evidence": None}
            for item in ("helmet", "high_visibility_vest", "steel_toe_boots", "safety_harness")
        },
        "site_hazards": [],
    }


def demo_crack_report(filename: str) -> dict[str, Any]:
    """Return an explicit, empty demo report without inferring image contents."""
    return {
        "analysis_status": "not_performed_demo_mode",
        "source_file": filename,
        "notice": "No image analysis was performed. Supply a Gemini API key to request AI analysis.",
        "defect_type": None,
        "estimated_crack_width_mm": None,
        "width_assessment": "Not assessed",
        "root_causes": [],
        "recommended_repairs": [],
        "urgency": "Not assessed",
        "visual_evidence": None,
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.IGNORECASE)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIServiceError("Gemini returned a response that was not valid JSON.") from exc
    if not isinstance(result, dict):
        raise AIServiceError("Gemini returned JSON in an unexpected format.")
    return result


def _gemini_image_request(api_key: str, image_bytes: bytes, mime_type: str, prompt: str) -> dict[str, Any]:
    try:
        from google.genai import types

        client = _create_gemini_client(api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config={"response_mime_type": "application/json", "temperature": 0.1},
        )
    except AIServiceError:
        raise
    except Exception as exc:
        raise _gemini_request_error(exc, api_key, "image analysis") from exc
    text = getattr(response, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise AIServiceError("Gemini returned an empty response; no report was created.")
    return _extract_json(text)


def analyze_safety_image(
    api_key: str, image_bytes: bytes, mime_type: str, filename: str
) -> dict[str, Any]:
    prompt = f"""
Analyze this construction-site photo for preliminary visual safety observations. Return ONLY JSON
with this schema:
{{
  "safety_score": number from 0 to 100 or null if the view is insufficient,
  "overall_status": "Needs review" | "Potential concerns" | "No obvious concern visible" | "Unable to assess",
  "ppe_detection": {{
    "helmet": {{"status": "observed_present" | "observed_absent" | "unclear", "evidence": string or null}},
    "high_visibility_vest": {{"status": "observed_present" | "observed_absent" | "unclear", "evidence": string or null}},
    "steel_toe_boots": {{"status": "observed_present" | "observed_absent" | "unclear", "evidence": string or null}},
    "safety_harness": {{"status": "observed_present" | "observed_absent" | "unclear", "evidence": string or null}}
  }},
  "site_hazards": [
    {{"hazard": string, "severity": "Low" | "Medium" | "High" | "Critical",
      "evidence": string, "corrective_remedy": string}}
  ]
}}
Do not infer PPE hidden by framing, distance, clothing, or image quality; use unclear. Do not claim legal
compliance or non-compliance from a photo. If a score is not defensible from visible evidence, return null.
Assess only visible conditions and state uncertainty. OSHA requirements depend on jurisdiction and task;
IS 456 is a concrete structural code, not a PPE standard. Do not imply either standard was formally audited.
"""
    report = _gemini_image_request(api_key, image_bytes, mime_type, prompt)
    score = report.get("safety_score")
    if score is not None and (
        not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100
    ):
        raise AIServiceError("Gemini returned an invalid safety_score; the report was not accepted.")
    statuses = {"Needs review", "Potential concerns", "No obvious concern visible", "Unable to assess"}
    if report.get("overall_status") not in statuses:
        raise AIServiceError("Gemini returned an invalid overall_status; the report was not accepted.")
    ppe = report.get("ppe_detection")
    expected_ppe = ("helmet", "high_visibility_vest", "steel_toe_boots", "safety_harness")
    if not isinstance(ppe, dict) or any(
        not isinstance(ppe.get(key), dict)
        or ppe[key].get("status") not in {"observed_present", "observed_absent", "unclear"}
        for key in expected_ppe
    ):
        raise AIServiceError("Gemini returned an invalid PPE checklist; the report was not accepted.")
    hazards = report.get("site_hazards")
    if not isinstance(hazards, list) or any(
        not isinstance(hazard, dict)
        or hazard.get("severity") not in {"Low", "Medium", "High", "Critical"}
        for hazard in hazards
    ):
        raise AIServiceError("Gemini returned invalid hazard data; the report was not accepted.")
    report.update(analysis_status="ai_generated_preliminary", source_file=filename)
    return report


def analyze_crack_image(
    api_key: str, image_bytes: bytes, mime_type: str, filename: str
) -> dict[str, Any]:
    prompt = f"""
Visually inspect this concrete/wall surface image for a preliminary defect hypothesis. Return ONLY JSON:
{{
  "defect_type": "Hairline" | "Settlement" | "Structural Shear" | "Thermal Expansion" | "Spalling" | "Unable to assess",
  "estimated_crack_width_mm": number or null,
  "width_assessment": string explaining whether an image scale/reference supports the estimate,
  "root_causes": [string],
  "recommended_repairs": [string],
  "urgency": "Routine" | "Soon" | "Urgent" | "Immediate" | "Unable to assess",
  "visual_evidence": string or null
}}
Do not estimate crack width from pixels or appearance unless a known scale/reference is visible in the image;
otherwise set width to null and explain why. Do not diagnose structural safety or prescribe a final repair.
State uncertainty. Epoxy injection or structural re-grouting may be mentioned only as options contingent
on an engineer's investigation and defect diagnosis. A qualified structural engineer must inspect on site.
"""
    report = _gemini_image_request(api_key, image_bytes, mime_type, prompt)
    allowed_types = {"Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling", "Unable to assess"}
    if report.get("defect_type") not in allowed_types:
        raise AIServiceError("Gemini returned an invalid defect_type; the report was not accepted.")
    width = report.get("estimated_crack_width_mm")
    if width is not None and (
        not isinstance(width, (int, float)) or isinstance(width, bool) or width < 0
    ):
        raise AIServiceError("Gemini returned an invalid crack width; the report was not accepted.")
    if report.get("urgency") not in {"Routine", "Soon", "Urgent", "Immediate", "Unable to assess"}:
        raise AIServiceError("Gemini returned an invalid urgency; the report was not accepted.")
    for field in ("root_causes", "recommended_repairs"):
        if not isinstance(report.get(field), list) or any(
            not isinstance(item, str) for item in report[field]
        ):
            raise AIServiceError(f"Gemini returned invalid {field}; the report was not accepted.")
    report.update(analysis_status="ai_generated_preliminary", source_file=filename)
    return report


def ask_engineering_assistant(api_key: str, history: list[dict[str, str]]) -> str:
    """Send text conversation history to Gemini and return its assistant response."""
    try:
        client = _create_gemini_client(api_key)
        contents = [
            {
                "role": "model" if item["role"] == "assistant" else "user",
                "parts": [{"text": item["content"]}],
            }
            for item in history
        ]
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": (
                    "You are a construction engineering information assistant. Give general, "
                    "cautious guidance, ask clarifying questions, do not present estimates as "
                    "measurements or certify safety/design/code compliance, and direct urgent "
                    "hazards to the site safety officer or qualified engineer."
                ),
                "temperature": 0.3,
            },
        )
    except AIServiceError:
        raise
    except Exception as exc:
        raise _gemini_request_error(exc, api_key, "assistant request") from exc
    text = getattr(response, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise AIServiceError("Gemini returned an empty assistant response.")
    return text.strip()


def format_inr(amount: float) -> str:
    """Format INR amounts in crores or lakhs, with Indian digit grouping."""
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:,.2f} Cr"
    if amount >= 100_000:
        return f"₹{amount / 100_000:,.2f} L"
    return f"₹{amount:,.0f}"


def calculate_plan(
    area_sqft: float,
    completion_pct: float,
    budget_rate_inr_sqft: float,
    valuation_rate_inr_sqft: float,
    steel_kg_sqft: float,
    cement_bags_sqft: float,
) -> dict[str, float]:
    """Calculate planning values solely from supplied rates and coefficients."""
    values = (area_sqft, completion_pct, budget_rate_inr_sqft, valuation_rate_inr_sqft, steel_kg_sqft, cement_bags_sqft)
    if any(value < 0 for value in values) or completion_pct > 100:
        raise ValueError("Planning inputs must be non-negative and completion must not exceed 100%.")
    total_budget = area_sqft * budget_rate_inr_sqft
    return {
        "total_budget_inr": total_budget,
        "pro_rata_capex_inr": total_budget * completion_pct / 100,
        "market_value_inr": area_sqft * valuation_rate_inr_sqft,
        "steel_kg": area_sqft * steel_kg_sqft,
        "cement_bags": area_sqft * cement_bags_sqft,
    }


def weather_advisory(condition: str) -> tuple[str, list[str]]:
    advisories = {
        "High Wind": (
            "Pause exposed lifting operations",
            [
                "Suspend crane and other lifting operations when site wind limits are reached; follow the lift plan and equipment manufacturer limits.",
                "Secure loose materials, temporary works, and elevated platforms; restrict access to exposed areas.",
                "Resume only after a competent person confirms conditions are within approved operating limits.",
            ],
        ),
        "Heavy Rain": (
            "Control water and electrical hazards",
            [
                "Inspect excavations, access routes, drainage, and temporary works for flooding or instability.",
                "Isolate and protect electrical equipment from water; keep personnel away from standing water near energized systems.",
                "Protect fresh concrete from washout and follow the approved mix and curing procedure before placing or finishing.",
            ],
        ),
        "Extreme Heat": (
            "Reduce heat-stress exposure",
            [
                "Provide drinking water, shaded rest, acclimatization, and work/rest cycles appropriate to site conditions.",
                "Watch for heat illness and use the site's emergency response plan; seek medical help for symptoms.",
                "Manage concrete placement, finishing, and curing under the approved method statement for hot-weather conditions.",
            ],
        ),
        "Normal": (
            "Maintain routine site controls",
            [
                "Continue pre-task briefings, PPE checks, housekeeping, and equipment inspections.",
                "Monitor changing weather and follow the approved task risk assessment and lift plans.",
            ],
        ),
    }
    if condition not in advisories:
        raise ValueError("Choose a listed weather condition.")
    return advisories[condition]
