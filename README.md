# Pulse Customer Analytics

A local Streamlit dashboard for transaction exports. It combines CSV and JSON inputs, reports rejected and duplicate rows, and calculates revenue, repeat purchasing, cohort retention, rolling churn, and RFM segments.

## Run

Python 3.10 or newer is required. From the repository root:

```bash
git clone https://github.com/AJAHANI16/Pulse-Customer-Analytics.git
cd Pulse-Customer-Analytics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m streamlit run app.py
```

Open <http://localhost:8501>. On Windows, activate the environment with `.venv\Scripts\Activate.ps1`. Use `python -m streamlit` from that environment so the app can import the installed package.

The app loads the bundled sample files on first use. The sidebar accepts one uploaded CSV or JSON file, then filters dates, countries, and acquisition channels. The audit describes ingestion before those filters; the CSV download contains the filtered rows.

## Inputs and ETL

| Column | Meaning |
| --- | --- |
| `customer_id` | Customer identifier |
| `transaction_id` | Unique transaction identifier |
| `transaction_date` | Purchase date or timestamp |
| `revenue` | Non-negative transaction revenue |
| `country` | Country label, normalized to uppercase |
| `acquisition_channel` | Channel label, normalized to title case |

All columns are required. JSON can be an array of objects or newline-delimited objects. The pipeline trims identifiers, parses dates in UTC, rejects invalid identifiers/dates and non-finite or negative revenue, and keeps the first valid occurrence of each transaction ID. Missing country/channel values are labeled Unknown. These labels are not validated against a fixed vocabulary.

The bundled demonstration has 250 input rows: 248 are accepted, one is invalid, and one is a duplicate. These are sample-data counts, not a reliability benchmark.

To combine files without opening the dashboard:

```bash
python -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
```

This writes `customer_transactions.csv` and `etl_report.json` under `data/processed/`. `--output-dir` selects another destination.

## Reading the charts

- **Revenue and growth:** sums by observed calendar month. Missing months are not inserted; growth compares successive observed months.
- **Repeat customer rate:** customers with multiple transactions divided by customers in the selected data.
- **Retention:** customers active in a later month divided by the size of their first-observed-purchase cohort. The dataset has no signup dates. Cohorts are recomputed after filtering.
- **Churn:** customers in the previous 30-day window who are absent from the current 30-day window, divided by previous-window customers. A window with no previous customers returns zero. Short histories show an explanation instead of a chart.
- **RFM:** percentile-based scores for recency, frequency, and monetary value. Recency is measured from one day after the latest selected transaction. Tied values share a score. Fewer than four customers are labeled Insufficient data. These are relative rules, not a trained prediction model.

## Code and checks

`src/analytics_dashboard/etl.py` handles ingestion and auditing; `metrics.py` contains the calculations; `app.py` renders the dashboard.

```bash
python -m pytest -q
python -m ruff check .
```

The tests cover ingestion, rejection counts, analytical calculations, and dashboard rendering, including small selections. [GitHub Actions](https://github.com/AJAHANI16/Pulse-Customer-Analytics/actions) runs the suite on pushes and pull requests.

This is an in-memory application with flat-file output. It has no database, scheduled incremental loading, authentication, or hosted deployment. Uploads are processed in temporary directories; the command-line pipeline writes to the destination you choose.

## License

MIT. See [LICENSE](LICENSE).
