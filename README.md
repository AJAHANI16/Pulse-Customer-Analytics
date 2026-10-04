# Pulse Customer Analytics Dashboard

A portfolio-ready analytics application that turns mixed CSV/JSON transaction exports into trustworthy customer insights. The automated Pandas ETL validates the schema, standardizes fields, removes bad records and duplicates, and writes an auditable quality report. The bundled dataset intentionally demonstrates a **99.2% processing success rate** (248 accepted of 250 input rows).

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB) ![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC) ![Style](https://img.shields.io/badge/style-ruff-D7FF64)

## What it includes

- Repeatable CSV and JSON ingestion with source lineage and explicit validation errors
- Cleaned, normalized transaction output plus a machine-readable ETL audit report
- Monthly revenue and growth, cohort retention, rolling 30-day churn, and RFM segmentation
- Interactive date, country, and acquisition-channel filters
- Plotly reports, customer drill-down, and filtered CSV export
- Unit tests and GitHub Actions CI

## Architecture

```text
data/raw (CSV + JSON) ──> load & validate ──> clean/deduplicate
                                                   │
                             audit JSON + clean CSV ┤
                                                   ▼
                                     metrics ──> Streamlit UI
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
analytics-etl data/raw/transactions.csv data/raw/transactions.json
streamlit run app.py
```

Open `http://localhost:8501`. The application starts with the included demo data, or use the sidebar to upload your own CSV/JSON file.

## Input schema

| Column | Type | Description |
| --- | --- | --- |
| `customer_id` | string | Stable customer identifier |
| `transaction_id` | string | Unique order identifier |
| `transaction_date` | date/datetime | Purchase timestamp |
| `revenue` | number | Non-negative order revenue |
| `country` | string | Customer country code |
| `acquisition_channel` | string | Marketing acquisition source |

Invalid dates, missing identifiers, negative/non-numeric revenue, and duplicate transaction IDs are rejected and counted in `data/processed/etl_report.json`.

## Definitions

- **Cohort retention:** share of customers from an acquisition-month cohort active in each later calendar month.
- **Rolling 30-day churn:** customers active in the prior 30-day window but absent from the current 30-day window, divided by prior-window active customers.
- **RFM segments:** quartile scores for recency, purchase frequency, and monetary value, grouped into At Risk, Needs Attention, Loyal, and Champions.
- **Repeat customer rate:** share of customers with more than one transaction in the current filter selection.

## Quality checks

```bash
pytest -q
ruff check .
analytics-etl data/raw/transactions.csv data/raw/transactions.json
```

## Repository layout

```text
app.py                          # Streamlit dashboard
src/analytics_dashboard/etl.py # pipeline and audit report
src/analytics_dashboard/metrics.py # analytical models
data/raw/                       # reproducible demo inputs
tests/                          # unit test suite
```

## License

MIT
