# ZipSheet — Sales Insight Automator

A full-stack web application with a **React** frontend and a **FastAPI** backend.  
Upload a sales CSV or Excel file and receive an AI-powered revenue summary.

## Project Structure

```
ZipSheet/
├── frontend/              # Vite + React (JavaScript)
│   ├── src/
│   │   ├── App.jsx        # Root component
│   │   ├── UploadForm.jsx # File-upload + email form
│   │   ├── App.css        # Component styles
│   │   └── index.css      # Global reset
│   ├── package.json
│   └── vite.config.js
├── backend/               # FastAPI (Python)
│   ├── main.py            # API entry-point
│   ├── services/
│   │   ├── parser.py      # Column normalizer & synonym mapper
│   │   └── summary.py     # Tolerant summary generator
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn main:app --reload      # http://localhost:8000
```

## Column Synonym Mapping

The parser normalises uploaded column headers (lower-case, strip whitespace,
replace non-alphanumeric characters with `_`) and matches them against these
synonym lists:

| Internal Key | Accepted Column Names |
|---|---|
| **revenue** | `revenue`, `value`, `amount`, `sales`, `turnover` |
| **category** | `product_category`, `product`, `industry_name`, `industry`, `industry_name_nzsioc` |
| **region** | `region`, `area`, `state`, `territory`, `district` |
| **status** | `status`, `order_status`, `shipment_status`, `order_state` |
| **units** | `units`, `unit`, `magnitude` |

When a non-standard header is matched, a mapping note is included in the
response warnings (e.g. `Mapped 'value' -> revenue`).

## Testing with curl

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@sample.csv" \
  -F "email=test@example.com"
```

Or open **http://localhost:8000/docs** for Swagger UI.