"""CSV cleaning module for Insight Engine.

Heuristically detects column kinds (money, date, percent, numeric, text, id),
normalizes values, collapses near-duplicate text labels via fuzzy matching,
drops duplicate rows, and emits a CleaningReport describing every change.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from io import BytesIO
from typing import Any, Callable

import pandas as pd
from rapidfuzz import fuzz, process

CURRENCY_RE = re.compile(r"[\$£€¥₹]")
MONEY_SUFFIX = {"k": 1e3, "m": 1e6, "b": 1e9}
DIRECTIONAL_ABBREV = {
    "n.": "North", "no.": "North", "nth.": "North",
    "s.": "South", "so.": "South", "sth.": "South",
    "e.": "East", "w.": "West",
}
DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y",
    "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y",
    "%d-%b-%Y", "%d-%B-%Y",
)


@dataclass
class ColumnReport:
    name: str
    original_dtype: str
    final_dtype: str
    detected_kind: str
    nulls_filled: int = 0
    rows_coerced: int = 0
    labels_collapsed: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class CleaningReport:
    rows_in: int
    rows_out: int
    duplicates_dropped: int
    columns: list[ColumnReport]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "duplicates_dropped": self.duplicates_dropped,
            "columns": [asdict(c) for c in self.columns],
        }


# ----------------------------- parsers -----------------------------

def parse_money(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("() ").strip()
    s = CURRENCY_RE.sub("", s).strip()
    multiplier = 1.0
    if s and s[-1].lower() in MONEY_SUFFIX:
        multiplier = MONEY_SUFFIX[s[-1].lower()]
        s = s[:-1].strip()
    s = s.replace(",", "")
    try:
        val = float(s) * multiplier
        return -val if negative else val
    except ValueError:
        return None


def parse_percent(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    if s.endswith("%"):
        try:
            return float(s[:-1].strip()) / 100.0
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_number(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(v: Any) -> pd.Timestamp | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            ts = pd.to_datetime(s, format=fmt)
            if not pd.isna(ts):
                return ts
        except (ValueError, TypeError):
            continue
    # Fallback: pandas auto-inference
    try:
        ts = pd.to_datetime(s, errors="raise")
        if not pd.isna(ts):
            return ts
    except (ValueError, TypeError):
        pass
    return None


# ----------------------------- detection -----------------------------

def _frac(values: list[str], predicate: Callable[[str], Any]) -> float:
    if not values:
        return 0.0
    return sum(1 for v in values if predicate(v) is not None) / len(values)


def detect_kind(series: pd.Series, name: str) -> str:
    name_lower = name.lower()

    raw = series.dropna().astype(str).str.strip()
    raw = raw[raw != ""]
    samples = raw.tolist()
    if not samples:
        return "text"
    n = len(samples)

    if name_lower == "id" or name_lower.endswith("_id"):
        if _frac(samples, parse_number) > 0.8:
            return "id"

    percent_share = sum(1 for v in samples if "%" in v) / n
    if percent_share > 0.3:
        return "percent"

    money_share = sum(1 for v in samples if CURRENCY_RE.search(v)) / n
    if money_share > 0.2:
        return "money"

    date_hint = any(h in name_lower for h in ("date", "time", "_at", "dob"))
    if date_hint and _frac(samples, parse_date) > 0.5:
        return "date"

    if _frac(samples, parse_number) > 0.7:
        return "numeric"

    if not date_hint and _frac(samples, parse_date) > 0.7:
        return "date"

    return "text"


# ----------------------------- text normalization -----------------------------

def _expand_directional_abbrevs(v: str) -> str:
    """Expand short directional tokens: 'N. America' -> 'North America'."""
    tokens = v.split()
    out: list[str] = []
    for tok in tokens:
        key = tok.lower()
        out.append(DIRECTIONAL_ABBREV.get(key, tok))
    return " ".join(out)


def _canonicalize_text(v: str) -> str:
    v = v.strip()
    if not v:
        return v
    # Expand "N." -> "North" before any other normalization
    v = _expand_directional_abbrevs(v)
    # Treat short alpha strings as acronyms (USA, EU, APAC, LATAM, EMEA).
    # Cap at 5 chars so real 6+ letter words like "EUROPE" / "FRANCE" fall
    # through to the title-case path instead.
    alnum = v.replace(".", "").replace(" ", "")
    if alnum.isalpha() and 2 <= len(alnum) <= 5:
        return alnum.upper()
    if v.isupper() or v.islower():
        return v.title()
    return v


def collapse_labels(values: pd.Series, threshold: int = 88) -> tuple[pd.Series, dict[str, str]]:
    """Collapse near-duplicate string labels using fuzzy matching.

    Returns the normalized series and a {original -> canonical} report of
    only the values that actually changed.
    """
    cleaned = values.fillna("").astype(str).str.strip()
    canon_initial = cleaned.map(_canonicalize_text)

    canonicals: list[str] = []
    fuzzy_map: dict[str, str] = {}

    counts = canon_initial[canon_initial != ""].value_counts()
    for value in counts.index:
        if canonicals:
            match = process.extractOne(
                value, canonicals,
                scorer=fuzz.token_set_ratio,
                processor=str.lower,
            )
            if match and match[1] >= threshold:
                fuzzy_map[value] = match[0]
                continue
        canonicals.append(value)
        fuzzy_map[value] = value

    out = cleaned.map(lambda v: fuzzy_map.get(_canonicalize_text(v), v) if v else "")

    changes: dict[str, str] = {}
    for orig in values.dropna().astype(str).str.strip().unique():
        if not orig:
            continue
        final = fuzzy_map.get(_canonicalize_text(orig), orig)
        if orig != final:
            changes[orig] = final
    return out, changes


# ----------------------------- main entry -----------------------------

def _apply_parser(series: pd.Series, parser: Callable[[Any], Any]) -> tuple[pd.Series, int, int]:
    """Apply parser; return (parsed, rows_coerced, rows_needing_imputation)."""
    parsed = series.map(parser)
    non_null_source = series.notna()
    coerced = int((non_null_source & parsed.notna()).sum())
    needs_imputation = int(parsed.isna().sum())
    return parsed, coerced, needs_imputation


def clean_csv(buf: bytes) -> tuple[pd.DataFrame, CleaningReport]:
    """Clean a CSV from raw bytes. Returns (cleaned_df, report)."""
    df = pd.read_csv(
        BytesIO(buf),
        dtype=str,
        keep_default_na=False,
        na_values=["", " ", "NA", "N/A", "n/a", "null", "NULL", "None", "none", "missing", "-"],
    )
    rows_in = len(df)

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    column_reports: list[ColumnReport] = []

    for col in df.columns:
        kind = detect_kind(df[col], col)
        report = ColumnReport(
            name=col,
            original_dtype="object",
            final_dtype="",
            detected_kind=kind,
        )
        series = df[col]

        if kind == "money":
            parsed, coerced, need_fill = _apply_parser(series, parse_money)
            report.rows_coerced = coerced
            if need_fill > 0:
                median = parsed.median()
                if pd.isna(median):
                    median = 0.0
                parsed = parsed.fillna(median)
                report.nulls_filled = need_fill
                report.notes.append(f"filled {need_fill} missing with median {median:.2f}")
            df[col] = parsed
            report.final_dtype = "float"

        elif kind == "percent":
            parsed, coerced, need_fill = _apply_parser(series, parse_percent)
            report.rows_coerced = coerced
            if need_fill > 0:
                median = parsed.median()
                if pd.isna(median):
                    median = 0.0
                parsed = parsed.fillna(median)
                report.nulls_filled = need_fill
                report.notes.append(f"filled {need_fill} missing with median {median:.4f}")
            df[col] = parsed
            report.final_dtype = "float"

        elif kind == "date":
            parsed, coerced, need_fill = _apply_parser(series, parse_date)
            report.rows_coerced = coerced
            report.nulls_filled = need_fill  # dates left null (not imputed)
            df[col] = parsed.map(
                lambda t: t.strftime("%Y-%m-%d") if t is not None and not pd.isna(t) else None
            )
            report.final_dtype = "date(iso-text)"
            if need_fill:
                report.notes.append(f"{need_fill} unparseable dates left as NULL")

        elif kind in ("numeric", "id"):
            parsed, coerced, need_fill = _apply_parser(series, parse_number)
            report.rows_coerced = coerced
            if kind == "numeric" and need_fill > 0:
                median = parsed.median()
                if pd.isna(median):
                    median = 0.0
                parsed = parsed.fillna(median)
                report.nulls_filled = need_fill
                report.notes.append(f"filled {need_fill} missing with median {median:g}")
            # Cast to nullable Int64 when the column is integer-valued (id, or
            # numeric with no fractional parts) — nicer dtype for SQLite + UI.
            non_null = parsed.dropna()
            if len(non_null) > 0 and (non_null == non_null.round()).all():
                parsed = parsed.round().astype("Int64")
                report.final_dtype = "int"
            else:
                report.final_dtype = "float"
            df[col] = parsed

        else:  # text
            collapsed, changes = collapse_labels(series)
            report.labels_collapsed = changes
            blanks = collapsed == ""
            report.nulls_filled = int(blanks.sum())
            collapsed = collapsed.where(~blanks, "Unknown")
            df[col] = collapsed
            report.final_dtype = "text"
            if changes:
                report.notes.append(f"collapsed {len(changes)} label variants")
            if report.nulls_filled:
                report.notes.append(f"filled {report.nulls_filled} blank cells with 'Unknown'")

        column_reports.append(report)

    pre_dedup = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    duplicates_dropped = pre_dedup - len(df)

    return df, CleaningReport(
        rows_in=rows_in,
        rows_out=len(df),
        duplicates_dropped=duplicates_dropped,
        columns=column_reports,
    )


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/messy_sales.csv")
    cleaned, report = clean_csv(path.read_bytes())
    print("=== Cleaning report ===")
    print(json.dumps(report.to_dict(), indent=2, default=str))
    print("\n=== Cleaned head ===")
    print(cleaned.head(10).to_string())
    print(f"\nShape: {cleaned.shape}")
    print("\nDtypes:")
    print(cleaned.dtypes)
