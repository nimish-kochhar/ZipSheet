"""
AI-powered summary generator (with deterministic fallback).

Takes a *profile dict* (from ``profiler.profile_dataframe``) and:
1. Builds a compact ``dataset_analysis`` text (capped columns to avoid
   token blow-up).
2. If ``GEMINI_API_KEY`` is available, calls the Gemini LLM for a polished
   executive summary.
3. Otherwise, produces a deterministic template-based fallback.

Returns ``{"summary": "...", "warnings": [...]}``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")

logger = logging.getLogger(__name__)

MAX_PROFILE_CHARS = 6_000  # safety cap for LLM input


# ─── build analysis text ──────────────────────────────

def _build_analysis_text(profile: dict[str, Any]) -> str:
    """Convert the profile dict into a compact text block for the LLM.

    Limits output to top-10 numeric and top-10 categorical columns to keep
    the prompt within a sensible token budget.
    """
    lines: list[str] = []

    lines.append(
        f"Dataset: {profile['n_rows']} rows × {profile['n_columns']} columns  |  "
        f"Total missing values: {profile['total_missing']}"
    )
    lines.append(f"Columns: {', '.join(profile['column_names'][:30])}")
    lines.append("")

    # numeric (top 10)
    num_stats = profile.get("numeric_stats", {})
    if num_stats:
        lines.append("=== Numeric Columns ===")
        for col in list(num_stats)[:10]:
            s = num_stats[col]
            lines.append(
                f"  {col}: sum={s['sum']}, mean={s['mean']}, "
                f"min={s['min']}, max={s['max']}, std={s['std']}, "
                f"count={s['count']}, missing={s['missing_count']}"
            )
        if len(num_stats) > 10:
            lines.append(f"  ... and {len(num_stats) - 10} more numeric columns")
        lines.append("")

    # categorical (top 10)
    cat_stats = profile.get("categorical_stats", {})
    if cat_stats:
        lines.append("=== Categorical Columns ===")
        for col in list(cat_stats)[:10]:
            s = cat_stats[col]
            top_str = ", ".join(
                f"{v['value']} ({v['count']})" for v in s["top_values"]
            )
            lines.append(
                f"  {col}: {s['unique_count']} unique | top: {top_str} | "
                f"missing={s['missing_count']}"
            )
        if len(cat_stats) > 10:
            lines.append(f"  ... and {len(cat_stats) - 10} more categorical columns")
        lines.append("")

    # datetime
    dt_stats = profile.get("datetime_stats", {})
    if dt_stats:
        lines.append("=== Datetime Columns ===")
        for col, s in dt_stats.items():
            lines.append(f"  {col}: from {s['min']} to {s['max']}")
        lines.append("")

    # sample rows
    samples = profile.get("sample_rows", [])
    if samples:
        lines.append("=== Sample Rows (first up to 5) ===")
        for i, row in enumerate(samples[:5], 1):
            lines.append(f"  Row {i}: {row}")

    text = "\n".join(lines)
    return text[:MAX_PROFILE_CHARS]


# ─── deterministic fallback ──────────────────────────

def _fallback_summary(profile: dict[str, Any]) -> str:
    """Template-based summary when no LLM is available."""
    parts: list[str] = []

    parts.append(
        f"Dataset contains {profile['n_rows']:,} rows and "
        f"{profile['n_columns']} columns."
    )

    total_missing = profile["total_missing"]
    if total_missing:
        pct = round(total_missing / (profile["n_rows"] * profile["n_columns"]) * 100, 1)
        parts.append(f"Total missing values: {total_missing:,} ({pct}% of all cells).")
    else:
        parts.append("No missing values detected — data appears complete.")

    # top numeric highlights
    num_stats = profile.get("numeric_stats", {})
    if num_stats:
        first_col = next(iter(num_stats))
        s = num_stats[first_col]
        parts.append(
            f"Numeric highlight — '{first_col}': "
            f"sum={s['sum']:,}, mean={s['mean']}, range=[{s['min']}, {s['max']}]."
        )

    # top categorical highlights
    cat_stats = profile.get("categorical_stats", {})
    if cat_stats:
        first_col = next(iter(cat_stats))
        s = cat_stats[first_col]
        top_val = s["top_values"][0]["value"] if s["top_values"] else "N/A"
        parts.append(
            f"Categorical highlight — '{first_col}': "
            f"{s['unique_count']} unique values, most frequent: '{top_val}'."
        )

    # datetime range
    dt_stats = profile.get("datetime_stats", {})
    if dt_stats:
        first_col = next(iter(dt_stats))
        s = dt_stats[first_col]
        parts.append(f"Date range in '{first_col}': {s['min']} to {s['max']}.")

    return "\n".join(parts)


# ─── public API ───────────────────────────────────────

def generate_summary_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Produce an executive summary from *profile*.

    Returns ``{"summary": "<text>", "warnings": [...]}``.
    """
    warnings: list[str] = []
    analysis_text = _build_analysis_text(profile)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.info("GEMINI_API_KEY not set — using deterministic fallback.")
        warnings.append("AI summary unavailable (no API key). Showing template summary.")
        return {"summary": _fallback_summary(profile), "warnings": warnings}

    # ── LLM path ──────────────────────────────────────
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        model = genai.GenerativeModel(model_name)

        prompt = (
            "You are a business analyst. Given the following dataset analysis, "
            "produce a concise executive summary with 3–6 bullet points and "
            "2 recommended actions. Use plain language suitable for a "
            "non-technical executive.\n\n"
            f"--- DATASET ANALYSIS ---\n{analysis_text}"
        )

        response = model.generate_content(prompt)
        summary = response.text.strip()
        return {"summary": summary, "warnings": warnings}

    except Exception as exc:
        logger.exception("LLM call failed — falling back to template summary")
        warnings.append(f"AI summary failed ({exc}). Showing template summary.")
        return {"summary": _fallback_summary(profile), "warnings": warnings}
