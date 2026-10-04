"""Reusable customer analytics calculations."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd


def monthly_revenue(data: pd.DataFrame) -> pd.DataFrame:
    result = (
        data.assign(month=data["transaction_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    result["growth_pct"] = result["revenue"].pct_change(fill_method=None).mul(100)
    return result


def customer_segments(data: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Create interpretable RFM segments from quartile scores."""
    snapshot = as_of or (pd.Timestamp(data["transaction_date"].max()) + timedelta(days=1))
    rfm = data.groupby("customer_id").agg(
        last_purchase=("transaction_date", "max"),
        frequency=("transaction_id", "nunique"),
        monetary=("revenue", "sum"),
    )
    rfm["recency_days"] = (snapshot - rfm["last_purchase"]).dt.days
    rfm["r_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    score = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)
    rfm["segment"] = pd.cut(
        score, bins=[0, 5, 8, 10, 12], labels=["At Risk", "Needs Attention", "Loyal", "Champions"]
    )
    return rfm.reset_index()


def cohort_retention(data: pd.DataFrame) -> pd.DataFrame:
    activity = data[["customer_id", "transaction_date"]].copy()
    activity["activity_month"] = activity["transaction_date"].dt.to_period("M")
    activity["cohort_month"] = activity.groupby("customer_id")["activity_month"].transform("min")
    activity["period"] = (activity["activity_month"] - activity["cohort_month"]).apply(lambda value: value.n)
    counts = activity.groupby(["cohort_month", "period"])["customer_id"].nunique().unstack(fill_value=0)
    cohort_size = counts[0]
    retention = counts.divide(cohort_size, axis=0).mul(100)
    retention.index = retention.index.astype(str)
    return retention


def rolling_churn(data: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """Return daily share of prior-window active customers absent in the current window."""
    first_day = pd.Timestamp(data["transaction_date"].min()).normalize()
    last_day = pd.Timestamp(data["transaction_date"].max()).normalize()
    window = timedelta(days=window_days)
    dates = pd.date_range(first_day + window, last_day)
    rows = []
    for day in dates:
        day = pd.Timestamp(day)
        previous_start = day - (window * 2)
        current_start = day - window
        previous = set(data.loc[(data.transaction_date > previous_start) & (data.transaction_date <= current_start), "customer_id"])
        current = set(data.loc[(data.transaction_date > current_start) & (data.transaction_date <= day), "customer_id"])
        churned = previous - current
        rows.append({"date": day, "churn_rate": len(churned) / len(previous) * 100 if previous else 0.0})
    return pd.DataFrame(rows)
