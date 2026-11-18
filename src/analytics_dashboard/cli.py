"""Command-line entry point for the ETL pipeline."""

import argparse

from analytics_dashboard.etl import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean customer transaction CSV/JSON files.")
    parser.add_argument("inputs", nargs="+", help="Input CSV or JSON files")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    args = parser.parse_args()
    _, report = run_pipeline(args.inputs, args.output_dir)
    print(
        f"Accepted {report.output_rows} of {report.input_rows} rows. "
        f"Rejected {report.rejected_rows}: "
        f"{report.invalid_rows} invalid, {report.duplicate_rows} duplicate."
    )


if __name__ == "__main__":
    main()
