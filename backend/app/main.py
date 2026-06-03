"""FastAPI application entry point."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .cleaning import clean_csv
from .pipeline import answer_question
from .schemas import (
    CleaningReportModel,
    QueryRequest,
    QueryResponse,
    UploadResponse,
)

load_dotenv()

app = FastAPI(title="Insight Engine API", version="0.1.0")

cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "table_loaded": str(db.table_exists())}


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    buf = await file.read()
    try:
        cleaned_df, report = clean_csv(buf)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    db.load_dataframe(cleaned_df)

    return UploadResponse(
        table=db.TABLE_NAME,
        report=CleaningReportModel(**report.to_dict()),
        table_schema=db.get_schema(),
        preview_rows=db.df_to_records(cleaned_df, n=10),
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")
    try:
        return answer_question(req.question.strip())
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
