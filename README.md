# Anarisuto – Mini Data Intelligence Tool

A mini data intelligence system:

- React frontend ( rsuite + chart.js ) for natural-language questions and chart display
- FastAPI backend that uses Gemini to parse *intent JSON*
- Deterministic backend query planner converts intent to safe SQL
- PostgreSQL stores products/sales and returns chart-ready data

## Setup

## 1) Start Postgres (with schema + seed)

From repo root:

```bash
docker compose up -d
```

This initializes the DB from [db/init/01_schema.sql](db/init/01_schema.sql) and [db/init/02_seed.sql](db/init/02_seed.sql). Test data has been added reflecting sales from a car dealership.

## 2) Run backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Recommended: add your Gemini key
# export GEMINI_API_KEY=...

uvicorn app.main:app --reload --port 8000
```

If you don’t have a Gemini key, set `LLM_MODE=stub` in `backend/.env`.

## 3) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Example questions

- "Show total revenue trend from 2020 to 2026"
- "Compare revenue in 2022 and 2026"
- "Revenue by category in 2024"
- "Top 3 products by revenue in 2026"

## API

- `POST /query` body: `{ "question": "..." }`
- response: `{ chartType, labels, datasets }`


## Why Intent-Based Parsing (and not direct LLM-to-SQL)

This project uses **intent-based parsing** instead of generating SQL directly from the LLM.

While LLMs can produce SQL, doing so introduces risks such as incorrect joins, invalid aggregations, unpredictable performance, and unsafe queries. Validating arbitrary SQL reliably witout running it is almost impossible.

Instead, the LLM is constrained to output **structured intent JSON** (metrics, dimensions, filters). The backend then maps this intent to **predefined, deterministic SQL templates**.

This approach ensures:
- Correct and predictable SQL
- Strong safety guarantees (no arbitrary joins, or delete instructions, etc )
- Clear separation between language understanding and database logic
- A production-aligned, scalable architecture

The trade-off favors reliability and correctness over flexibility, which is critical for real-world data systems.

## Note

The current version is implemented as a proof-of-concept to validate the approach.  
As a result, only a limited set of intents, patterns, and SQL templates are included.

The system is designed to be easily extensible by adding additional intents, patterns, and corresponding SQL templates.

Demo Video
[https://youtu.be/rCguybg_PB8](https://youtu.be/rCguybg_PB8)
