# ZipSheet — Sales Insight Automator

Upload any sales CSV/XLSX → get an AI-powered executive summary emailed to you.

## Architecture

```
┌────────────┐  POST /analyze   ┌──────────────┐
│  React UI  │ ───────────────▸ │  FastAPI API  │
│  (Vite)    │ ◂─── JSON ───── │  port 8000    │
│  port 3000 │                  └──┬───┬───┬────┘
└────────────┘                     │   │   │
                          profile_df  Gemini  SendGrid
                          (pandas)    (LLM)   (email)
```

- **Frontend** — React 19 + Vite, drag-drop upload, collapsible profile, copy-to-clipboard.
- **Backend** — FastAPI, schema-agnostic profiler, Gemini AI summariser with deterministic fallback, SendGrid email (or console log).
- **CI** — GitHub Actions: build frontend + install backend deps on every PR to `main`.

## Run Locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn main:app --reload     # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## Run with Docker

```bash
# 1. Add keys to .env at repo root (see below)
# 2. Build & start
docker-compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
# Swagger  → http://localhost:8000/docs
```

Stop: `docker-compose down` · Rebuild: `docker-compose up --build`

## Environment Variables

Create a `.env` file at the repo root:

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | No | Google Gemini API key (falls back to template summary) |
| `GEMINI_MODEL` | No | Model name override (default `gemini-2.0-flash`) |
| `SENDGRID_API_KEY` | No | SendGrid key (falls back to console log) |
| `EMAIL_FROM` | No | Sender address (default `noreply@zipsheet.app`) |
| `VITE_API_URL` | No | Backend URL for frontend (default `http://localhost:8000`) |
| `CORS_ORIGIN` | No | Allowed CORS origin (default `http://localhost:5173`) |

## Security Notes

- **Never commit `.env`** — it is git-ignored.
- **No raw data sent to LLM** — only the profiled stats and a small sample (max 5 rows) are sent; profile text is truncated to 6 000 chars.
- **File size** — consider adding an upload size limit in production (e.g. nginx `client_max_body_size`).

## Test with curl

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@sample.csv" \
  -F "email=test@example.com"
```

Or open **http://localhost:8000/docs** for the interactive Swagger UI.

## Submission Checklist

- [ ] GitHub repo link
- [ ] Live frontend URL
- [ ] Swagger docs URL (`/docs`)
- [ ] This README