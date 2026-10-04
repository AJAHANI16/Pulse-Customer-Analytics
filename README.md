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

## What we built and verified

The complete project was published in this independent repository. It contains:

- An installable `analytics_dashboard` package with ingestion, transformation, analytical functions, and a CLI.
- CSV/JSON ingestion with source-file lineage; required-column checks; identifier trimming; country/channel normalization; date/revenue conversion; invalid-row rejection; transaction-ID deduplication; and sorting by date.
- A cleaned transaction CSV and a JSON audit with input/output counts, invalid and duplicate counts, and a processing success rate.
- Monthly revenue and month-over-month growth calculations, first-purchase-month cohort retention, rolling 30-day churn, and recency/frequency/monetary (RFM) segmentation.
- A Streamlit dashboard with uploads, filters, four KPI cards, Plotly charts, customer tables, audit display, and filtered CSV downloads.
- Packaging, a command-line entry point, nine automated tests, Ruff linting, GitHub Actions CI, demo inputs, and an MIT license.

Three import-format issues were corrected to make the current Ruff checks pass. The published implementation passed lint and all **nine tests** in GitHub Actions, including a Streamlit AppTest that checks dashboard rendering and the four KPI labels. These checks cover the bundled demo and selected ETL/metric cases; they do not prove every upload or filter combination works.

GitHub stores the source code. The dashboard runs on your computer using the steps below; a hosted dashboard has not been deployed.

## Install and start the dashboard

Use Python 3.10 or newer. CI uses Python 3.12. Run all commands from the repository root, which contains `app.py` and `pyproject.toml`.

### macOS / Linux: first-time setup

Open Terminal and run:

```bash
git clone https://github.com/AJAHANI16/Pulse-Customer-Analytics.git
cd Pulse-Customer-Analytics
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
.venv/bin/python -m streamlit run app.py
```

If you already cloned the repository, skip the clone command and enter that directory. Open [http://localhost:8501](http://localhost:8501) after Streamlit starts. Keep the terminal running while using the app; press **Ctrl+C** there to stop it.

Using `.venv/bin/python` explicitly ensures that installation and Streamlit use the same environment. A bare `streamlit` command can accidentally launch a globally installed Anaconda version instead.

### Start again later

```bash
cd /path/to/Pulse-Customer-Analytics
.venv/bin/python -m streamlit run app.py
```

Replace the path with your clone location. You do not need to reinstall each time.

### Windows PowerShell

```powershell
git clone https://github.com/AJAHANI16/Pulse-Customer-Analytics.git
cd Pulse-Customer-Analytics
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## How to use the dashboard

1. **Explore the demo:** the app automatically processes both bundled files on first load; no upload is needed.
2. **Read the KPI cards:** Revenue totals accepted revenue; Customers counts unique customers; Avg. order value averages transaction revenue; Repeat customer rate measures customers with multiple transactions.
3. **Set filters:** choose dates, countries, and channels in the sidebar. KPIs and charts update using the selected transactions. An empty result displays a warning.
4. **Explore the analysis:** inspect revenue trends and the channel breakdown, then use the Retention, Churn, and Segments tabs. The Segments tab includes customer-level recency, frequency, and revenue.
5. **Inspect the audit:** expand **Data quality & pipeline audit** to see ingestion counts. These counts describe the dataset before dashboard filters.
6. **Export:** click **Download cleaned data** to download cleaned transactions matching the current filters.
7. **Upload your data:** choose a `.csv` or `.json` file in the sidebar with the columns below. The dashboard accepts one uploaded file at a time; the CLI can combine multiple files.

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

For JSON, use an array of objects with these field names. The ETL also attempts newline-delimited JSON when ordinary JSON parsing fails; use the `.json` extension. Missing required columns raise an error. Country/channel columns must exist, but their values are not checked against a fixed list. Dates are parsed in UTC and saved without timezone information.

## Run ETL without the dashboard

```bash
.venv/bin/python -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
```

For your own files and a custom destination:

```bash
.venv/bin/python -m analytics_dashboard.cli /path/to/orders.csv /path/to/orders.json --output-dir data/processed/custom
```

The default run writes `data/processed/customer_transactions.csv` and `data/processed/etl_report.json`. The installed `.venv/bin/analytics-etl` command is an equivalent entry point on macOS/Linux. Generated CSV/JSON outputs in `data/processed/` are ignored by Git.

The bundled inputs deliberately contain **250 rows**, with **248 accepted**, **1 invalid**, and **1 duplicate**. Expected CLI output:

```text
Processed 248/250 rows (99.20% success).
```

The **99.2%** figure is a reproducible result on the bundled demo, not a measured production reliability rate.

## Definitions

- **Cohort retention:** share of customers from a first-observed-purchase-month cohort active in each later calendar month.
- **Rolling 30-day churn:** customers active in the prior 30-day window but absent from the current 30-day window, divided by prior-window active customers.
- **RFM segments:** quartile scores for recency, purchase frequency, and monetary value, grouped into At Risk, Needs Attention, Loyal, and Champions.
- **Repeat customer rate:** share of customers with more than one transaction in the current filter selection.

Cohort membership and RFM scores are recomputed after filtering. The cohort date is the first purchase observed in that selection, rather than a separately stored signup date. RFM recency defaults to one day after the latest selected transaction. Monthly growth compares consecutive observed months; months without transactions are not inserted into the revenue series. Churn returns 0% when the preceding window has no active customers.

## Quality checks

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m analytics_dashboard.cli data/raw/transactions.csv data/raw/transactions.json
```

The nine tests cover schema rejection, normalization/deduplication, mixed-file ingestion, persistence, revenue, retention, segmentation, churn bounds, and dashboard rendering. See the latest [GitHub Actions results](https://github.com/AJAHANI16/Pulse-Customer-Analytics/actions).

## Troubleshooting

### `ModuleNotFoundError: No module named 'analytics_dashboard'`

The package lives under `src/` and must be installed in the environment running Streamlit. Stop the current server with **Ctrl+C**, enter your clone directory, and run:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -c "import sys, analytics_dashboard; print(sys.executable); print(analytics_dashboard.__file__)"
.venv/bin/python -m streamlit run app.py
```

If the import check succeeds but bare `streamlit run app.py` fails, the bare command points to another Python installation. Continue using the explicit `.venv/bin/python -m streamlit` command.

### Input files cannot be found

Launch from the repository root. Default data paths are relative to the working directory.

### Port 8501 is already in use

Stop the earlier Streamlit process, or use another port:

```bash
.venv/bin/python -m streamlit run app.py --server.port 8502
```

Open `http://localhost:8502` for that instance.

### Get updates from GitHub

Run `git pull --ff-only` in your clone directory, then restart Streamlit. Reinstall the package if dependencies changed.

## Current scope and limitations

- This is a local portfolio/demo application using in-memory Pandas and flat files. It has no database, incremental loading, authentication, or hosted deployment.
- RFM quartiles are not robust for very small customer selections. Churn plotting can fail for histories shorter than 30 days. The default demo is covered by the rendering test.
- Uploads and pipeline outputs use shared filenames under `data/processed/`; the current app is intended for a single user rather than concurrent sessions.

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
