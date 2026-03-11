"""
AI-powered summary generator.

Takes the dataset analysis text and sends it to Google Gemini
to produce a professional executive summary.
"""

import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configure Gemini ──────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """\
You are a senior data analyst. Given the dataset analysis below, write a
concise, professional executive summary (max 300 words). Include:

1. A brief overview of what the dataset appears to contain.
2. Key numeric highlights (totals, averages, ranges).
3. Notable categorical patterns.
4. Data quality observations (missing values, anomalies).
5. Actionable insights or recommendations.

Use clear headings, bullet points, and plain business language.
Do NOT include raw code or JSON — the audience is a non-technical executive.
"""


async def generate_ai_summary(analysis_text: str) -> dict:
    """
    Send *analysis_text* to Gemini and return
    ``{"summary": "...", "ai_powered": True/False, "error": "..." | None}``.

    Falls back to returning the raw analysis text if the API key is missing
    or if the model call fails, so the endpoint never crashes.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — returning raw analysis instead.")
        return {
            "summary": analysis_text,
            "ai_powered": False,
            "error": "GEMINI_API_KEY not configured. Showing raw dataset analysis.",
        }

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n--- DATASET ANALYSIS ---\n{analysis_text}"
        )

        summary = response.text.strip()
        return {
            "summary": summary,
            "ai_powered": True,
            "error": None,
        }

    except Exception as exc:
        logger.exception("Gemini API call failed")
        return {
            "summary": analysis_text,
            "ai_powered": False,
            "error": f"AI summary generation failed: {exc}. Showing raw analysis.",
        }
