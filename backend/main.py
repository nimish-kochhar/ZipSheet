"""ZipSheet backend – FastAPI entry-point (scaffold only)."""

from fastapi import FastAPI

app = FastAPI(title="ZipSheet API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
