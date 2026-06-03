"""SQLite storage for the cleaned dataset."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "insight.db"
TABLE_NAME = "dataset"
_DANGEROUS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|attach|detach|pragma|vacuum|reindex|replace)\b",
    re.IGNORECASE,
)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            future=True,
            connect_args={"check_same_thread": False},
        )
    return _engine


def load_dataframe(df: pd.DataFrame, table: str = TABLE_NAME) -> None:
    df.to_sql(table, get_engine(), if_exists="replace", index=False)


def get_schema(table: str = TABLE_NAME) -> dict[str, str]:
    with get_engine().connect() as conn:
        rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return {row[1]: row[2] for row in rows}


def get_sample_rows(table: str = TABLE_NAME, n: int = 3) -> list[dict[str, Any]]:
    with get_engine().connect() as conn:
        result = conn.execute(text(f'SELECT * FROM "{table}" LIMIT :n'), {"n": n})
        cols = list(result.keys())
        return [dict(zip(cols, row)) for row in result.fetchall()]


def table_exists(table: str = TABLE_NAME) -> bool:
    with get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": table},
        ).fetchone()
    return row is not None


def validate_sql_static(sql: str) -> None:
    """Reject mutations and multi-statement queries before execution."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        raise ValueError("Empty SQL")
    if ";" in stripped:
        raise ValueError("Only single-statement queries are allowed")
    if _DANGEROUS.search(stripped):
        raise ValueError("Only SELECT statements are allowed")
    first = stripped.split(None, 1)[0].upper()
    if first not in ("SELECT", "WITH"):
        raise ValueError(f"Query must start with SELECT or WITH, got {first}")


def validate_sql_executes(sql: str) -> str | None:
    """Return an error string if SQLite can't plan the query, None if it can."""
    try:
        validate_sql_static(sql)
        with get_engine().connect() as conn:
            conn.execute(text(f"EXPLAIN {sql}"))
        return None
    except Exception as e:
        return str(e)


def execute_query(sql: str) -> tuple[list[str], list[list[Any]]]:
    validate_sql_static(sql)
    with get_engine().connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
    return cols, rows


def df_to_records(df: pd.DataFrame, n: int | None = None) -> list[dict[str, Any]]:
    """JSON-safe records, handling pandas NA / Int64 / NaN."""
    sub = df.head(n) if n is not None else df
    return json.loads(sub.to_json(orient="records", date_format="iso"))
