# Insight Engine

Hackathon project: upload a messy sales CSV → automatic cleaning + cleaning
report → SQLite → NL question → SQL + chart + plain-English insight.

## Stack

- **Backend**: Python 3.11+, FastAPI, pandas, SQLAlchemy + SQLite, rapidfuzz,
  managed with `uv`
- **LLM**: pluggable via `LLM_PROVIDER` env var
  - `hf` (default) → Hugging Face Inference API (`HF_TOKEN`, `HF_MODEL`)
  - `anthropic` → Claude API (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`)
  - The user prefers HF as default; **don't hardcode Anthropic-only**
- **Frontend**: Vite + React 18 + TypeScript, recharts, plain CSS (no UI lib)

## Run

```powershell
# backend
cd backend
uv sync                                          # one-time
uv run uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install                                      # one-time
npm run dev                                      # serves http://localhost:5173
```

Vite proxies `/api/*` → `http://127.0.0.1:8000` (see `frontend/vite.config.ts`),
so the browser never hits the backend directly during dev. CORS is also wired
in `app/main.py` for direct access.

`.env` lives at `backend/.env` (gitignored). `.env.example` is the template.

## Quick verifications

```powershell
# cleaning module against the sample CSV (no LLM needed)
cd backend
uv run python -m app.cleaning data/messy_sales.csv

# frontend type-check / build
cd frontend
npx tsc -b
npm run build
```

## Directory map

```
backend/app/
  main.py        # FastAPI: /upload, /query, /health, CORS
  cleaning.py    # CSV -> cleaned DataFrame + CleaningReport
  db.py          # SQLite load + schema introspection + SQL guardrails
  llm.py         # HFProvider, AnthropicProvider, get_llm() factory
  pipeline.py    # generate plan -> validate w/ EXPLAIN -> retry once -> execute -> synthesize insight
  schemas.py     # Pydantic request/response models
backend/data/
  messy_sales.csv  # sample messy dataset for the demo
  insight.db       # SQLite, created on first /upload (gitignored)
frontend/src/
  App.tsx, api.ts, types.ts, styles.css
  components/Uploader.tsx, CleaningSummary.tsx, ChatInput.tsx,
             DataTable.tsx, ChartView.tsx, Insight.tsx
```

## Conventions / non-obvious bits

- **Single-table model.** Each `/upload` *replaces* the `dataset` table — there
  is no multi-file or multi-table support. The LLM prompt is built fresh from
  the current schema + 3 sample rows on every `/query`.
- **Cleaning kind detection** (`cleaning.detect_kind`) is heuristic and
  threshold-based on a string sample of each column. Order matters:
  percent → money (currency symbol) → date (with name hint) → numeric →
  fallback date → text. Tweak thresholds in `detect_kind`, not by adding new
  parsers at random.
- **Acronym preservation.** `_canonicalize_text` keeps short (2–5 char) all-alpha
  uppercase strings (USA, EU, APAC, LATAM) and title-cases longer all-caps words
  (EUROPE → Europe). The 5-char cap is deliberate — bumping it to 6 makes
  `EUROPE`/`FRANCE` get treated as acronyms.
- **Directional abbreviations** (`N.`, `S.`, `E.`, `W.`) are expanded before
  fuzzy matching so `N. America` collapses into `North America`. Fuzzy matching
  alone won't bridge that gap because token_set_ratio scores it ~70.
- **Fuzzy label collapsing** uses `processor=str.lower` so case variants match
  before canonicalization. Threshold 88 on `fuzz.token_set_ratio` — lowering
  this risks collapsing distinct products like `Widget A`/`Widget B`.
- **Int64 casting for `id`/whole-number `numeric` columns**: nicer dtype in
  SQLite and the UI; preserves nulls (unlike plain `int64`).
- **SQL guardrails are layered:**
  1. `db.validate_sql_executes(sql)` runs `EXPLAIN <sql>` against SQLite (catches
     syntax/column-name errors) — used for the retry loop in the pipeline.
  2. `db.validate_sql_static(sql)` rejects multi-statement, non-`SELECT/WITH`,
     and dangerous keywords (`INSERT|UPDATE|DELETE|DROP|...`). Called inside
     `execute_query` so it runs immediately before execution. Don't remove
     either layer — they catch different failure modes.
- **LLM JSON parsing** (`pipeline._extract_json`) strips markdown fences and
  finds the outermost `{...}`. HF chat-completion models sometimes wrap output
  in ```` ```json ```` despite the prompt — that's why the fence strip exists.
- **Pipeline retry budget is 1.** If the LLM produces invalid SQL twice, we
  raise. Don't loop further without changing the prompt.
- **Chart spec** is best-effort. `ChartView` falls back to first/second column
  if the LLM-named columns aren't present. `type=none` is a valid signal that
  we shouldn't render a chart.

## Frontend conventions

- Components are function components with `Props` type aliases at the top of
  the file. Plain CSS classes; no CSS modules, no Tailwind.
- All API calls go through `src/api.ts`; the proxy means components fetch
  `/api/upload` and `/api/query` regardless of where the backend lives.
- `tsconfig.json` has `noUnusedLocals` + `noUnusedParameters` on. Keep them on.

## Intentionally out of scope

No auth, no Docker, no CI/CD, no vector DB or RAG, no knowledge graph / Neo4j,
no voice input, no source connectors beyond CSV, no multi-user state. Don't
add these without checking with the user first — the scope was explicitly
limited for the hackathon demo.

## Memory notes

- User prefers HF-first LLM abstraction with paid APIs as a switchable
  alternative. See `~/.claude/.../memory/user_llm_preference.md`.
- User prefers incremental delivery for multi-stage build requests: ship one
  stage, wait for explicit "go ahead". See `feedback_incremental_builds.md`.
