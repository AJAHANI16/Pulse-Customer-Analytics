import pandas as pd
import pytest

from analytics_dashboard.metrics import (
    cohort_retention,
    customer_segments,
    monthly_revenue,
    rolling_churn,
)


@pytest.fixture
def transactions():
    return pd.DataFrame(
        {
            "customer_id": ["A", "B", "A", "C", "A", "B", "D", "E"],
            "transaction_id": [f"T{i}" for i in range(8)],
            "transaction_date": pd.to_datetime(["2024-01-05", "2024-01-10", "2024-02-08", "2024-02-15", "2024-03-02", "2024-03-12", "2024-03-20", "2024-04-20"]),
            "revenue": [10, 20, 15, 40, 30, 5, 50, 60],
        }
    )


def test_monthly_revenue(transactions):
    result = monthly_revenue(transactions)
    assert result.revenue.tolist() == [30, 55, 85, 60]
    assert result.iloc[1].growth_pct == pytest.approx(83.3333)


def test_cohort_retention(transactions):
    result = cohort_retention(transactions)
    assert result.loc["2024-01", 0] == 100
    assert result.loc["2024-01", 1] == 50


def test_segments_include_every_customer(transactions):
    result = customer_segments(transactions, pd.Timestamp("2024-05-01"))
    assert result.customer_id.nunique() == transactions.customer_id.nunique()
    assert result.segment.notna().all()


def test_rolling_churn_is_bounded(transactions):
    result = rolling_churn(transactions)
    assert result.churn_rate.between(0, 100).all()


def test_short_history_preserves_churn_columns(transactions):
    result = rolling_churn(transactions.iloc[:1])
    assert result.empty
    assert list(result.columns) == ["date", "churn_rate"]


def test_single_customer_is_not_given_a_quartile_segment(transactions):
    result = customer_segments(transactions[transactions.customer_id == "A"])
    assert result.segment.tolist() == ["Insufficient data"]
    assert result.r_score.isna().all()


def test_tied_customers_share_rfm_scores(transactions):
    data = transactions.iloc[:5].copy()
    data["customer_id"] = list("ABCDE")
    data["revenue"] = 10
    data["transaction_date"] = pd.Timestamp("2024-01-01")
    result = customer_segments(data)
    assert result[["r_score", "f_score", "m_score"]].drop_duplicates().shape[0] == 1
