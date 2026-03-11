"""ZipSheet backend – FastAPI entry-point."""

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.ai_service import generate_summary_from_profile
from services.email_service import send_email
from services.profiler import profile_dataframe, read_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZipSheet API")

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ── Analyze endpoint ──────────────────────────────────
ALLOWED_EXTENSIONS = (".csv", ".xlsx")


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    email: str = Form(...),
):
    # --- validate file type ---
    filename = file.filename or ""
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a .csv or .xlsx file.",
        )

    # --- read file ---
    try:
        contents = await file.read()
        df = read_file(contents, filename)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse the file: {exc}",
        )

    logger.info(
        "Parsed %d rows × %d cols from '%s'", len(df), len(df.columns), filename
    )

    # --- profile ---
    profile = profile_dataframe(df)

    # --- AI summary ---
    ai_result = generate_summary_from_profile(profile)
    summary_text = ai_result["summary"]

    # --- send email ---
    try:
        email_status = send_email(email, "Sales Summary", summary_text)
    except RuntimeError as exc:
        logger.error("Email send failed: %s", exc)
        email_status = {"sent": False, "error": str(exc)}

    return {
        "status": "success",
        "summary": summary_text,
        "warnings": ai_result.get("warnings", []),
        "email_status": email_status,
        "profile_snippet": {
            "n_rows": profile["n_rows"],
            "n_columns": profile["n_columns"],
            "total_missing": profile["total_missing"],
            "column_names": profile["column_names"],
            "numeric_columns": profile["numeric_columns"],
            "categorical_columns": profile["categorical_columns"],
            "datetime_columns": profile["datetime_columns"],
            "sample_rows": profile["sample_rows"][:5],
        },
    }
