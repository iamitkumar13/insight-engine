"""NL question -> SQL -> insight pipeline."""
from __future__ import annotations

import json
import re
from typing import Any

from . import db
from .llm import LLMProvider, get_llm
from .schemas import ChartSpec, QueryResponse

GEN_SYSTEM = """You are a data analyst. Translate a user's natural-language question about a SQLite table into a SQL query, and choose an appropriate chart type for the result.

Hard rules:
- Output ONLY a single JSON object. No prose, no markdown fences.
- The SQL must be a single SQLite SELECT statement (or a single statement starting with WITH).
- Do not use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, ATTACH, PRAGMA, or VACUUM.
- Reference only the table and columns provided in the schema.
- Limit results to 100 rows unless the question clearly asks for more.
- Date columns are stored as ISO text 'YYYY-MM-DD'. You can compare them as strings or use strftime().
- Quote identifiers with double quotes only if they contain spaces or reserved words.

JSON shape:
{
  "sql": "<the SQL>",
  "chart_spec": {
    "type": "bar" | "line" | "pie" | "none",
    "x": "<column name or null>",
    "y": "<column name or null>",
    "series": "<column name or null>"
  }
}

Chart guidance:
- Time series over a date column -> "line" with x = date column, y = metric
- Comparison across categories (region, product) -> "bar" with x = category, y = metric
- Share of a whole, <=8 slices -> "pie" with x = category, y = metric
- Single number, raw table, or no useful chart -> "none"
"""

SYNTH_SYSTEM = """You are a data analyst. Given a user's question and the rows returned by a SQL query, write 1 to 3 sentences of plain-English insight.

- Cite specific numbers, categories, or dates from the rows.
- Do not restate the question.
- Do not mention SQL, tables, or columns by name.
- If the result is empty, say so plainly and suggest what the user might try instead.
- Round large numbers reasonably (e.g., $12,345 -> $12.3K).
"""


def _format_schema_for_prompt(
    schema: dict[str, str], samples: list[dict[str, Any]]
) -> str:
    lines = [f"Table: {db.TABLE_NAME}", "Columns:"]
    for col, typ in schema.items():
        lines.append(f"  - {col} ({typ})")
    if samples:
        lines.append("")
        lines.append("Sample rows:")
        for s in samples:
            lines.append(f"  {json.dumps(s, default=str)}")
    return "\n".join(lines)


def _extract_json(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Could not find JSON in LLM output: {raw_text[:200]}")
    return json.loads(cleaned[start : end + 1])


def _coerce_chart_spec(raw: Any) -> ChartSpec:
    if not isinstance(raw, dict):
        return ChartSpec(type="none")
    kind = (raw.get("type") or "none").lower()
    if kind not in {"bar", "line", "pie", "none"}:
        kind = "none"
    return ChartSpec(
        type=kind,
        x=raw.get("x") or None,
        y=raw.get("y") or None,
        series=raw.get("series") or None,
    )


def _generate_plan(
    llm: LLMProvider,
    question: str,
    schema: dict[str, str],
    samples: list[dict[str, Any]],
    prior_sql: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    user = _format_schema_for_prompt(schema, samples) + f"\n\nQuestion: {question}"
    if prior_sql and error:
        user += (
            f"\n\nYour previous SQL failed:\n  SQL: {prior_sql}\n  Error: {error}\n"
            "Return a corrected JSON object."
        )
    raw = llm.complete(GEN_SYSTEM, user, max_tokens=800, temperature=0.0)
    return _extract_json(raw)


def _synthesize_insight(
    llm: LLMProvider,
    question: str,
    cols: list[str],
    rows: list[list[Any]],
) -> str:
    preview_rows = rows[:30]
    user = (
        f"Question: {question}\n"
        f"Columns: {cols}\n"
        f"Rows ({len(rows)} total, showing up to 30):\n"
        + "\n".join(json.dumps(r, default=str) for r in preview_rows)
    )
    return llm.complete(SYNTH_SYSTEM, user, max_tokens=300, temperature=0.2).strip()


def answer_question(question: str) -> QueryResponse:
    if not db.table_exists():
        raise RuntimeError("No dataset has been uploaded yet")

    schema = db.get_schema()
    samples = db.get_sample_rows(n=3)
    llm = get_llm()

    plan = _generate_plan(llm, question, schema, samples)
    sql = (plan.get("sql") or "").strip().rstrip(";")
    chart_spec_raw = plan.get("chart_spec", {})

    err = db.validate_sql_executes(sql)
    if err:
        plan = _generate_plan(llm, question, schema, samples, prior_sql=sql, error=err)
        sql = (plan.get("sql") or "").strip().rstrip(";")
        chart_spec_raw = plan.get("chart_spec", chart_spec_raw)
        err = db.validate_sql_executes(sql)
        if err:
            raise RuntimeError(f"Could not generate valid SQL after retry: {err}")

    cols, rows = db.execute_query(sql)
    insight = _synthesize_insight(llm, question, cols, rows)

    return QueryResponse(
        sql=sql,
        columns=cols,
        rows=rows,
        chart_spec=_coerce_chart_spec(chart_spec_raw),
        insight=insight,
    )
