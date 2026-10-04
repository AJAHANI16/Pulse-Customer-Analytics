"""Load, validate, clean, and persist customer activity data."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "customer_id",
    "transaction_id",
    "transaction_date",
    "revenue",
    "country",
    "acquisition_channel",
}


@dataclass(frozen=True)
class ETLReport:
    input_rows: int
    output_rows: int
    rejected_rows: int
    success_rate: float
    duplicate_rows: int
    invalid_rows: int

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def _read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".json":
        try:
            return pd.read_json(path)
        except ValueError:
            return pd.read_json(path, lines=True)
    raise ValueError(f"Unsupported file type: {path}. Use CSV or JSON.")


def load_sources(paths: Iterable[str | Path]) -> pd.DataFrame:
    """Load and concatenate CSV/JSON files with source lineage."""
    frames: list[pd.DataFrame] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        frame = _read_file(path)
        frame["source_file"] = path.name
        frames.append(frame)
    if not frames:
        raise ValueError("At least one input file is required.")
    return pd.concat(frames, ignore_index=True)


def transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, ETLReport]:
    """Normalize the schema and reject invalid or duplicate transactions."""
    missing = REQUIRED_COLUMNS.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    data = raw.copy()
    input_rows = len(data)
    for column in ("customer_id", "transaction_id", "country", "acquisition_channel"):
        data[column] = data[column].astype("string").str.strip()
    data["country"] = data["country"].str.upper()
    data["acquisition_channel"] = data["acquisition_channel"].str.title()
    data["transaction_date"] = pd.to_datetime(data["transaction_date"], errors="coerce", utc=True)
    data["revenue"] = pd.to_numeric(data["revenue"], errors="coerce")

    invalid_mask = (
        data["customer_id"].isna()
        | data["transaction_id"].isna()
        | data["transaction_date"].isna()
        | data["revenue"].isna()
        | (data["revenue"] < 0)
        | (data["customer_id"] == "")
        | (data["transaction_id"] == "")
    )
    invalid_rows = int(invalid_mask.sum())
    valid = data.loc[~invalid_mask].copy()
    duplicate_mask = valid.duplicated(subset="transaction_id", keep="first")
    duplicate_rows = int(duplicate_mask.sum())
    clean = valid.loc[~duplicate_mask].sort_values("transaction_date").reset_index(drop=True)
    clean["transaction_date"] = clean["transaction_date"].dt.tz_convert(None)

    rejected_rows = invalid_rows + duplicate_rows
    report = ETLReport(
        input_rows=input_rows,
        output_rows=len(clean),
        rejected_rows=rejected_rows,
        success_rate=round((len(clean) / input_rows * 100) if input_rows else 0.0, 2),
        duplicate_rows=duplicate_rows,
        invalid_rows=invalid_rows,
    )
    return clean, report


def run_pipeline(paths: Iterable[str | Path], output_dir: str | Path) -> tuple[pd.DataFrame, ETLReport]:
    """Execute ETL and write a clean dataset plus an audit report."""
    clean, report = transform(load_sources(paths))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    clean.to_csv(destination / "customer_transactions.csv", index=False)
    (destination / "etl_report.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return clean, report
