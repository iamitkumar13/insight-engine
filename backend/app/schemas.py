"""Pydantic models for FastAPI request/response shapes."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ColumnReportModel(BaseModel):
    name: str
    original_dtype: str
    final_dtype: str
    detected_kind: str
    nulls_filled: int
    rows_coerced: int
    labels_collapsed: dict[str, str]
    notes: list[str]


class CleaningReportModel(BaseModel):
    rows_in: int
    rows_out: int
    duplicates_dropped: int
    columns: list[ColumnReportModel]


class UploadResponse(BaseModel):
    table: str
    report: CleaningReportModel
    table_schema: dict[str, str] = Field(..., description="column_name -> sql type")
    preview_rows: list[dict[str, Any]]


class QueryRequest(BaseModel):
    question: str


class ChartSpec(BaseModel):
    type: str = Field(..., description="bar | line | pie | none")
    x: str | None = None
    y: str | None = None
    series: str | None = None


class QueryResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    chart_spec: ChartSpec
    insight: str
