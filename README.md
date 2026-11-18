# Pulse Customer Analytics

A Streamlit dashboard for reviewing customer transaction exports. Load CSV or JSON files, inspect rejected rows, and explore purchasing patterns by date, country, and acquisition channel.

## Run locally

Use Python 3.10 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m streamlit run app.py
```

Open <http://localhost:8501>. On Windows, activate the environment with `.venv\Scripts\Activate.ps1`. Run Streamlit through the environment's Python so it can find the installed package.

The app starts with the bundled sample data. Upload one CSV or JSON file in the sidebar to use your own transactions. Filters apply to the KPI cards, charts, customer table, and CSV download. The ingestion audit describes the input before filtering.

## Transaction format

| Column | Expected value |
| --- | --- |
| `customer_id` | Customer identifier |
| `transaction_id` | Unique transaction identifier |
| `transaction_date` | Purchase date or timestamp |
| `revenue` | Finite, non-negative transaction revenue |
| `country` | Country label |
| `acquisition_channel` | Marketing channel label |

All columns are required. JSON may be an array of objects or newline-delimited objects. The pipeline trims identifiers, parses dates in UTC, normalizes country/channel labels, rejects invalid records, and keeps the first valid occurrence of each transaction ID. Missing country/channel values become `UNKNOWN` and `Unknown`; labels are not checked against a fixed vocabulary.

The bundled files contain 250 sample rows: 248 accepted, one invalid, and one duplicate. They demonstrate ingestion behavior and chart rendering.

## How the metrics are defined

- **Revenue:** sum of transaction revenue in the selection. Monthly growth compares consecutive observed months; missing months are not inserted.
- **Average order value:** mean transaction revenue in the selection.
- **Repeat customer rate:** share of selected customers with more than one transaction.
- **Cohort retention:** share of a first-observed-purchase-month cohort active in a later month. Cohorts are recomputed after filtering. There are no signup dates in the input.
- **Rolling churn:** customers active in the previous 30-day window but absent from the current one, divided by previous-window customers. No previous customers gives zero. Short histories show an explanation instead of a chart.
- **RFM segments:** relative recency, frequency, and revenue scores within the selected customers. Ties receive the same score. Recency is measured from one day after the latest selected transaction; fewer than four customers gives `Insufficient data`. Segment names are rule-based labels.

## Command-line ingestion

The CLI accepts multiple files:

```bash
python -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
```

It prints accepted, invalid, and duplicate row counts, then writes `customer_transactions.csv` and `etl_report.json` under `data/processed/`. Use `--output-dir` for a different destination. The report's `success_rate` field is the percentage of input rows accepted; it is not a service reliability measure.

## Development

- `app.py`: dashboard controls and charts
- `src/analytics_dashboard/etl.py`: file loading, validation, and audit output
- `src/analytics_dashboard/metrics.py`: customer metrics
- `tests/`: ingestion, metric, and dashboard checks

```bash
python -m pytest -q
python -m ruff check .
```

[GitHub Actions](https://github.com/AJAHANI16/Pulse-Customer-Analytics/actions) runs these checks on pushes and pull requests.

The application processes data in memory. Uploads use temporary directories; the CLI writes to the chosen output directory. There is no database, incremental loader, authentication, or hosted deployment.

## License

[MIT](LICENSE).
