"""ZipSheet backend – FastAPI entry-point."""

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.email_service import send_email
from services.parser import analyze_dataset, analysis_to_text, read_file
from services.summary import generate_ai_summary

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

    # --- generic analysis ---
    analysis = analyze_dataset(df)
    analysis_text = analysis_to_text(analysis)

    # --- AI summary ---
    ai_result = await generate_ai_summary(analysis_text)
    summary_text = ai_result["summary"]

    # --- send email ---
    try:
        email_status = send_email(email, "Sales Summary", summary_text)
    except RuntimeError as exc:
        logger.error("Email send failed: %s", exc)
        email_status = {"sent": False, "error": str(exc)}

    return {
        "status": "success",
        "email": email,
        "summary": summary_text,
        "ai_powered": ai_result["ai_powered"],
        "email_status": email_status,
        "dataset_overview": {
            "rows": analysis["rows"],
            "columns": analysis["columns"],
            "column_names": analysis["column_names"],
            "numeric_columns": analysis["numeric_columns"],
            "categorical_columns": analysis["categorical_columns"],
            "datetime_columns": analysis["datetime_columns"],
            "missing_values": analysis["missing_values"],
        },
        "warnings": [ai_result["error"]] if ai_result["error"] else [],
    }
