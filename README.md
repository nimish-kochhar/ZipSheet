# ZipSheet

A full-stack web application with a **React** frontend and a **FastAPI** backend.

## Project Structure

```
ZipSheet/
├── frontend/          # Vite + React (JavaScript)
│   ├── src/           # React source code
│   ├── public/        # Static assets
│   ├── package.json   # Node dependencies & scripts
│   └── vite.config.js # Vite configuration
├── backend/           # FastAPI (Python)
│   ├── main.py        # Application entry-point
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Frontend

```bash
cd frontend
npm install      # first time only
npm run dev      # http://localhost:5173
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn main:app --reload    # http://localhost:8000
```