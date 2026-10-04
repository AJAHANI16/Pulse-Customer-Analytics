import json

import pandas as pd
import pytest

from analytics_dashboard.etl import load_sources, run_pipeline, transform


def valid_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [" C1 ", "C1", "C2"],
            "transaction_id": ["T1", "T1", "T2"],
            "transaction_date": ["2024-01-01", "2024-01-01", "bad"],
            "revenue": ["12.50", "12.50", "8"],
            "country": ["us", "us", "ca"],
            "acquisition_channel": ["organic", "organic", "email"],
        }
    )


def test_transform_cleans_and_reports_rejections():
    clean, report = transform(valid_rows())
    assert len(clean) == 1
    assert clean.iloc[0]["customer_id"] == "C1"
    assert clean.iloc[0]["country"] == "US"
    assert report.duplicate_rows == 1
    assert report.invalid_rows == 1
    assert report.success_rate == 33.33


def test_missing_schema_is_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        transform(pd.DataFrame({"customer_id": ["C1"]}))


def test_load_sources_supports_csv_and_json(tmp_path):
    one = valid_rows().iloc[:1]
    one.to_csv(tmp_path / "one.csv", index=False)
    one.to_json(tmp_path / "two.json", orient="records")
    loaded = load_sources([tmp_path / "one.csv", tmp_path / "two.json"])
    assert len(loaded) == 2
    assert set(loaded.source_file) == {"one.csv", "two.json"}


def test_pipeline_writes_outputs(tmp_path):
    source = tmp_path / "input.csv"
    valid_rows().iloc[:1].to_csv(source, index=False)
    _, report = run_pipeline([source], tmp_path / "out")
    saved_report = json.loads((tmp_path / "out/etl_report.json").read_text())
    assert (tmp_path / "out/customer_transactions.csv").exists()
    assert saved_report == report.to_dict()
