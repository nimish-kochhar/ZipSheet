"""
Generic dataset analyzer.

Reads any CSV/XLSX file and produces a structured analysis dictionary
with metadata, column types, statistics, missing values, and sample rows.
"""

import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def read_file(contents: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or XLSX bytes into a DataFrame."""
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
    return df


def analyze_dataset(df: pd.DataFrame) -> dict:
    """
    Return a rich analysis dict for *any* DataFrame.

    Keys returned
    -------------
    rows, columns, column_names,
    numeric_columns, categorical_columns, datetime_columns,
    numeric_stats, categorical_stats,
    missing_values, sample_rows
    """
    # ── basic metadata ────────────────────────────────
    rows, cols = df.shape
    column_names = list(df.columns)

    # ── detect column types ───────────────────────────
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = list(df.select_dtypes(include=["object", "category"]).columns)

    # attempt datetime parsing for object columns that look like dates
    datetime_cols: list[str] = []
    for col in list(categorical_cols):  # iterate copy
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if parsed.notna().sum() > len(df) * 0.5:  # >50 % parsed ok
                datetime_cols.append(col)
                categorical_cols.remove(col)
        except Exception:
            pass

    datetime_cols += list(df.select_dtypes(include="datetime").columns)

    # ── numeric stats ─────────────────────────────────
    numeric_stats: dict[str, dict] = {}
    for col in numeric_cols:
        s = df[col].dropna()
        numeric_stats[col] = {
            "mean": round(float(s.mean()), 2) if len(s) else None,
            "min": round(float(s.min()), 2) if len(s) else None,
            "max": round(float(s.max()), 2) if len(s) else None,
            "sum": round(float(s.sum()), 2) if len(s) else None,
            "std": round(float(s.std()), 2) if len(s) > 1 else None,
        }

    # ── categorical stats ─────────────────────────────
    categorical_stats: dict[str, list[dict]] = {}
    for col in categorical_cols:
        top = df[col].value_counts().head(5)
        categorical_stats[col] = [
            {"value": str(v), "count": int(c)} for v, c in top.items()
        ]

    # ── missing values ────────────────────────────────
    missing = df.isnull().sum()
    missing_values = {
        col: int(missing[col]) for col in column_names if missing[col] > 0
    }

    # ── sample rows (first 5) ─────────────────────────
    sample_rows = (
        df.head(5)
        .fillna("N/A")
        .astype(str)
        .to_dict(orient="records")
    )

    return {
        "rows": rows,
        "columns": cols,
        "column_names": column_names,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "missing_values": missing_values,
        "sample_rows": sample_rows,
    }


def analysis_to_text(analysis: dict) -> str:
    """Convert the analysis dict into a human-readable text block for the LLM."""
    lines: list[str] = []

    lines.append(f"Dataset Overview: {analysis['rows']} rows × {analysis['columns']} columns")
    lines.append(f"Columns: {', '.join(analysis['column_names'])}")
    lines.append("")

    # numeric
    if analysis["numeric_stats"]:
        lines.append("=== Numeric Column Statistics ===")
        for col, stats in analysis["numeric_stats"].items():
            lines.append(
                f"  {col}: mean={stats['mean']}, min={stats['min']}, "
                f"max={stats['max']}, sum={stats['sum']}, std={stats['std']}"
            )
        lines.append("")

    # categorical
    if analysis["categorical_stats"]:
        lines.append("=== Categorical Column Top Values ===")
        for col, values in analysis["categorical_stats"].items():
            top_str = ", ".join(f"{v['value']} ({v['count']})" for v in values)
            lines.append(f"  {col}: {top_str}")
        lines.append("")

    # datetime
    if analysis["datetime_columns"]:
        lines.append(f"Datetime columns detected: {', '.join(analysis['datetime_columns'])}")
        lines.append("")

    # missing
    if analysis["missing_values"]:
        lines.append("=== Missing Values ===")
        for col, count in analysis["missing_values"].items():
            pct = round(count / analysis["rows"] * 100, 1)
            lines.append(f"  {col}: {count} missing ({pct}%)")
        lines.append("")

    # sample
    lines.append("=== Sample Rows (first 5) ===")
    for i, row in enumerate(analysis["sample_rows"], 1):
        lines.append(f"  Row {i}: {row}")

    return "\n".join(lines)
