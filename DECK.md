# Insight Engine — Project Deck (content)

> Paste each slide below into PowerPoint / Google Slides / Canva, then export as
> **PDF** named `TeamName_Deck.pdf` (≤ 10 slides, ≤ 20 MB). Replace
> `TeamName` with your actual team name. Screenshots: capture from your running
> app (or the live link once deployed).

---

## Slide 1 — Title

**Insight Engine**
*From messy sales CSV → clean data → plain-English insights, in seconds.*

- Team: **Amit Kumar** (solo) — Full-stack & AI integration
- GitHub: github.com/iamitkumar13/insight-engine
- [Hackathon name / date]

---

## Slide 2 — Problem statement

**Business users sit on messy spreadsheets they can't query.**

- Real sales data is dirty: `$1,200`, `$2.5k`, `(50)` refunds, mixed date
  formats, duplicate region labels (`N. America`, `north america`, `EUROPE`),
  missing values, duplicate rows.
- Answering "which region is most profitable?" means manual cleanup in Excel +
  someone who can write SQL.
- Non-technical staff are blocked; analysts waste hours on janitorial data work.

> **The gap:** there's no tool that takes a raw CSV and lets *anyone* ask
> questions in plain English — cleaning, querying, and explaining included.

---

## Slide 3 — Solution overview

**Upload a CSV → ask a question → get SQL + chart + a plain-English answer.**

1. **Upload** a messy sales CSV.
2. **Auto-clean**: parse money/dates, collapse duplicate labels, fill missing
   values, drop dupes — with a transparent "What we cleaned" report.
3. **Ask** in natural language: *"Which regions have the highest total sales?"*
4. **Get** the generated SQL, a data table, a chart, and a 1–3 sentence
   takeaway.

> No SQL knowledge required. No manual cleanup. Full transparency on every
> transformation.

---

## Slide 4 — Live demo flow (screenshots)

*(Insert 3 screenshots from your running app)*

1. **Upload + "What we cleaned" panel** — 33 → 31 rows, 2 dupes dropped, region
   labels collapsed, money strings parsed, missing ages filled with median.
2. **Question + result** — the NL question, the generated SQL, and the data
   table.
3. **Chart + insight** — the chart and the plain-English takeaway.

> Tip: use the bundled `messy_sales.csv` for a consistent, impressive demo.

---

## Slide 5 — Architecture diagram

```
                    ┌──────────────────────────────────────┐
                    │  Frontend — React + TypeScript (Vite) │
                    │  Uploader · CleaningSummary · Chat     │
                    │  DataTable · ChartView · Insight       │
                    └───────────────┬──────────────────────┘
                                    │  /api (proxy)
                                    ▼
        ┌───────────────────────────────────────────────────────┐
        │  Backend — FastAPI (Python 3.11)                        │
        │                                                         │
        │  /upload ─► cleaning.py ─► pandas clean + report        │
        │                     │                                   │
        │                     ▼                                   │
        │                 db.py (SQLite)  ◄── single "dataset"    │
        │                     ▲                                   │
        │  /query ─► pipeline.py ─────────────────────┐           │
        │             1. build prompt (schema+rows)   │           │
        │             2. LLM → {sql, chart_spec}      │           │
        │             3. EXPLAIN validate + guardrail │           │
        │             4. execute → 5. LLM insight     │           │
        └─────────────────────────┼───────────────────┘           │
                                   ▼
                    ┌──────────────────────────────┐
                    │  LLM provider (pluggable)     │
                    │  Hugging Face (default) /      │
                    │  Anthropic Claude (switchable) │
                    └──────────────────────────────┘
```

---

## Slide 6 — How the cleaning works

**Heuristic, transparent, threshold-based (`cleaning.py`):**

- **Kind detection** per column: percent → money → date → numeric → text.
- **Money**: strips `$£€¥₹`, `(123)` → −123, `1.2k`/`3M` suffixes.
- **Dates**: tries multiple formats → normalizes to ISO.
- **Labels**: title-case, preserve acronyms (APAC, LATAM), expand directional
  abbreviations (`N. America` → `North America`), fuzzy-match near-duplicates
  (rapidfuzz).
- **Missing**: median for numeric, `"Unknown"` for text.
- **Dedupe**: drop exact-duplicate rows after normalization.

> Every change is reported back to the user — nothing is silently altered.

---

## Slide 7 — AI integration details

**Two LLM calls per question, with hard guardrails:**

1. **NL → SQL (plan):** prompt built from the live table schema + 3 sample rows;
   model returns `{sql, chart_spec}` as JSON.
2. **Insight synthesis:** a second call turns the result rows into a 1–3 sentence
   plain-English takeaway.

**Safety / reliability:**
- Generated SQL is validated with SQLite `EXPLAIN` (one retry on error).
- Static guardrail: `SELECT`/`WITH` only; rejects multi-statement & dangerous
  keywords.
- **Pluggable provider** — Hugging Face (`Qwen2.5-Coder-32B`) by default,
  Anthropic Claude switchable via one env var. **No vendor lock-in.**

---

## Slide 8 — Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Vite, recharts |
| Backend | FastAPI, pandas, SQLAlchemy + SQLite, rapidfuzz |
| AI | Hugging Face Inference API (default) / Anthropic Claude |
| Tooling | `uv` (Python), `npm` (Node), Claude Code (dev assist) |
| Deploy | Render (backend) + Vercel (frontend) |

---

## Slide 9 — What's next

- Multi-table / multi-file support and joins.
- Persistent storage (Postgres) for saved datasets & history.
- Saved questions, dashboards, and scheduled refresh.
- Confidence scoring on generated SQL; user-editable SQL.
- Export insights to PDF / share links.

---

## Slide 10 — Team

**Amit Kumar** — Solo developer
- Role: Full-stack engineering (backend, frontend) + AI integration + design
- Built the cleaning pipeline, NL→SQL pipeline, guardrails, and UI.
- Contact: 13abhirajamit@gmail.com
- GitHub: github.com/iamitkumar13

*Thank you — questions welcome.*
