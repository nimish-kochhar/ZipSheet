"""
Schema-agnostic data profiler.

Analyses *any* pandas DataFrame and returns a rich profile dictionary
containing column-type detection, per-column statistics, dataset-level
metrics, and a small sample for preview.

The profile is a plain ``dict`` — easy to serialise, test, and pass to
downstream consumers (AI summariser, API response, etc.).
"""

from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd


# ── helpers ───────────────────────────────────────────

def _norm(name: str) -> str:
    """Lower-case, strip, replace non-alphanumeric with ``_``."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def read_file(contents: bytes, filename: str) -> pd.DataFrame:
    """Read CSV / XLSX bytes into a DataFrame (columns NOT yet normalised)."""
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(contents))
    return pd.read_excel(io.BytesIO(contents), engine="openpyxl")


# ── main profiler ─────────────────────────────────────

def profile_dataframe(
    df: pd.DataFrame,
    *,
    max_sample_rows: int = 5,
    top_n: int = 5,
) -> dict[str, Any]:
    """Return a comprehensive profile dict for *df*.

    Parameters
    ----------
    df : DataFrame
        Raw DataFrame (columns will be normalised internally).
    max_sample_rows : int
        Number of sample rows to include in the profile.
    top_n : int
        How many top-frequency values to return for categorical columns.

    Returns
    -------
    dict  with keys:
        n_rows, n_columns, total_missing, column_names,
        numeric_columns, categorical_columns, datetime_columns,
        numeric_stats, categorical_stats, datetime_stats,
        sample_rows
    """
    # normalise column names
    df = df.copy()
    df.columns = [_norm(c) for c in df.columns]

    n_rows, n_cols = df.shape
    column_names = list(df.columns)

    # ── detect column types ───────────────────────────
    numeric_cols = list(df.select_dtypes(include="number").columns)

    cat_cols = list(df.select_dtypes(include=["object", "category"]).columns)

    datetime_cols: list[str] = list(df.select_dtypes(include="datetime").columns)
    # heuristic: try parsing object columns as dates
    for col in list(cat_cols):
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > n_rows * 0.5:
                datetime_cols.append(col)
                cat_cols.remove(col)
        except Exception:
            pass

    # ── numeric stats ─────────────────────────────────
    numeric_stats: dict[str, dict[str, Any]] = {}
    for col in numeric_cols:
        s = df[col]
        non_null = s.dropna()
        numeric_stats[col] = {
            "sum": round(float(non_null.sum()), 2) if len(non_null) else None,
            "mean": round(float(non_null.mean()), 2) if len(non_null) else None,
            "min": round(float(non_null.min()), 2) if len(non_null) else None,
            "max": round(float(non_null.max()), 2) if len(non_null) else None,
            "std": round(float(non_null.std()), 2) if len(non_null) > 1 else None,
            "count": int(non_null.count()),
            "missing_count": int(s.isna().sum()),
        }

    # ── categorical stats ─────────────────────────────
    categorical_stats: dict[str, dict[str, Any]] = {}
    for col in cat_cols:
        s = df[col]
        top = s.value_counts().head(top_n)
        categorical_stats[col] = {
            "unique_count": int(s.nunique()),
            "top_values": [
                {"value": str(v), "count": int(c)} for v, c in top.items()
            ],
            "missing_count": int(s.isna().sum()),
        }

    # ── datetime stats ────────────────────────────────
    datetime_stats: dict[str, dict[str, Any]] = {}
    for col in datetime_cols:
        s = pd.to_datetime(df[col], errors="coerce").dropna()
        datetime_stats[col] = {
            "min": str(s.min()) if len(s) else None,
            "max": str(s.max()) if len(s) else None,
            "sample": [str(v) for v in s.head(3).tolist()],
        }

    # ── dataset-level ─────────────────────────────────
    total_missing = int(df.isna().sum().sum())

    # ── sample rows ───────────────────────────────────
    sample_rows = (
        df.head(max_sample_rows)
        .fillna("N/A")
        .astype(str)
        .to_dict(orient="records")
    )

    return {
        "n_rows": n_rows,
        "n_columns": n_cols,
        "total_missing": total_missing,
        "column_names": column_names,
        "numeric_columns": numeric_cols,
        "categorical_columns": cat_cols,
        "datetime_columns": datetime_cols,
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "datetime_stats": datetime_stats,
        "sample_rows": sample_rows,
    }
