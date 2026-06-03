# Insight Engine

Turn a messy sales CSV into plain-English insights. Upload a CSV, the backend
cleans it (inconsistent dates, money strings, duplicate region labels, missing
values, dupe rows), loads it into SQLite, and answers natural-language questions
with a data table, a chart, and a 1–3 sentence takeaway.

## Stack

- **Backend** — Python 3.11+, FastAPI, pandas, SQLAlchemy, SQLite, rapidfuzz
- **LLM** — pluggable: Hugging Face Inference API (default) or Anthropic Claude
- **Frontend** — React 18 + TypeScript + Vite, recharts
- **Package mgmt** — `uv` for Python, `npm` for Node

## Prerequisites

- Python ≥ 3.11
- Node ≥ 18 (tested on 24)
- [`uv`](https://docs.astral.sh/uv/) — install via `pip install uv` or
  `irm https://astral.sh/uv/install.ps1 | iex`
- An LLM API key (one of):
  - **Hugging Face**: free read token at <https://huggingface.co/settings/tokens>
  - **Anthropic**: <https://console.anthropic.com/settings/keys>

## Setup

### 1. Backend

```powershell
cd backend
copy .env.example .env
# edit .env and fill in HF_TOKEN (or set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY)
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Backend is at <http://127.0.0.1:8000>. Interactive docs at
<http://127.0.0.1:8000/docs>.

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend is at <http://localhost:5173>. Vite proxies `/api/*` to the backend, so
you don't need to touch CORS for local dev.

## Demo flow

1. Open <http://localhost:5173>.
2. Drop `backend/data/messy_sales.csv` onto the uploader.
3. Watch the **What we cleaned** panel: 33 → 31 rows, 2 dupes dropped, region
   labels collapsed (`north america`, `N. America`, `EUROPE`, `europe`, `apac`,
   `latam`, `Latam` → `North America`, `Europe`, `APAC`, `LATAM`), money strings
   parsed (`$1,200`, `$2.5k`, `(50)` for refund), 4 missing ages filled with the
   median.
4. Try a question like:
   - *Which regions have the highest total sales?*
   - *Which product has the best profit margin?*
   - *Show monthly sales trend*
   - *Which regions have high sales but low profit margins?*
5. The result shows the SQL the LLM generated, a data table, a chart, and a
   plain-English takeaway.

## Switching LLM providers

Edit `backend/.env`:

```ini
# Open-source via Hugging Face Inference API
LLM_PROVIDER=hf
HF_TOKEN=hf_xxx
HF_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct

# Or Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Restart the backend after editing.

## Project structure

```
.
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── app/
│   │   ├── main.py           # FastAPI: /upload, /query, /health
│   │   ├── cleaning.py       # CSV cleaning + CleaningReport
│   │   ├── db.py             # SQLite load + SQL guardrails
│   │   ├── llm.py            # HF / Anthropic provider abstraction
│   │   ├── pipeline.py       # analyze → SQL → validate/retry → execute → insight
│   │   └── schemas.py        # Pydantic request/response models
│   └── data/
│       └── messy_sales.csv   # sample messy dataset
├── frontend/
│   ├── package.json
│   ├── vite.config.ts        # /api proxy to backend
│   └── src/
│       ├── App.tsx
│       ├── api.ts
│       ├── types.ts
│       ├── styles.css
│       └── components/       # Uploader, CleaningSummary, ChatInput,
│                             # DataTable, ChartView, Insight
└── README.md
```

## How it works

**Cleaning pipeline** (`app/cleaning.py`):

- Detects column kind from values (money, percent, date, numeric, id, text)
- Parses money: strips `$£€¥₹`, handles `(123)` → -123, `1.2k`/`3M` suffixes
- Parses dates: tries `YYYY-MM-DD`, `MM/DD/YYYY`, `Mon DD, YYYY`, etc. → ISO
- Collapses text labels: title-cases, preserves short acronyms (APAC, LATAM),
  expands directional abbreviations (`N. America` → `North America`), fuzzy-matches
  near-duplicates with rapidfuzz
- Imputes missing: median for numeric/money/percent, `"Unknown"` for text
- Drops exact-duplicate rows after normalization

**Query pipeline** (`app/pipeline.py`):

1. Build a prompt with the table schema + 3 sample rows
2. LLM returns `{sql, chart_spec}` as JSON
3. SQLite validates with `EXPLAIN` — if it errors, one retry with the error
   text appended to the prompt
4. Static guardrail: reject anything not `SELECT`/`WITH`, reject multi-statement
5. Execute, then a second LLM call synthesizes a 1–3 sentence insight from the
   question + result rows

## Out of scope (intentional)

No auth, no multi-user, no Docker, no vector DB / RAG, no Neo4j, no other data
source connectors. CSV in, SQLite, NL out — that's it.

## Troubleshooting

- **`HF_TOKEN is required when LLM_PROVIDER=hf`** — fill in `backend/.env`.
- **HF inference returns 503 / model loading** — that endpoint cold-starts.
  Either wait ~30 s and retry, switch to a smaller model
  (`mistralai/Mistral-7B-Instruct-v0.3`), or set `LLM_PROVIDER=anthropic`.
- **`Could not generate valid SQL after retry`** — the LLM produced two
  unparseable queries. Try rephrasing the question with column names from the
  *What we cleaned* panel.
- **Frontend can't reach backend** — make sure uvicorn is on port 8000 (the
  proxy in `vite.config.ts` targets `127.0.0.1:8000`).
