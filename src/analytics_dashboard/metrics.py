"""Reusable customer analytics calculations."""

from __future__ import annotations

from datetime import timedelta
from math import ceil

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
    """Score recency, frequency, and revenue relative to the selected customers."""
    snapshot = as_of or (pd.Timestamp(data["transaction_date"].max()) + timedelta(days=1))
    rfm = data.groupby("customer_id").agg(
        last_purchase=("transaction_date", "max"),
        frequency=("transaction_id", "nunique"),
        monetary=("revenue", "sum"),
    )
    rfm["recency_days"] = (snapshot - rfm["last_purchase"]).dt.days
    if len(rfm) < 4:
        for column in ("r_score", "f_score", "m_score"):
            rfm[column] = pd.Series(pd.NA, index=rfm.index, dtype="Int64")
        rfm["segment"] = "Insufficient data"
        return rfm.reset_index()
    for source, target in (
        ("recency_days", "r_score"),
        ("frequency", "f_score"),
        ("monetary", "m_score"),
    ):
        scores = rfm[source].rank(method="average", pct=True).mul(4).apply(ceil).clip(1, 4)
        rfm[target] = 5 - scores if source == "recency_days" else scores
    score = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)
    rfm["segment"] = pd.cut(
        score, bins=[0, 5, 8, 10, 12], labels=["At Risk", "Needs Attention", "Loyal", "Champions"]
    )
    return rfm.reset_index()


def cohort_retention(data: pd.DataFrame) -> pd.DataFrame:
    activity = data[["customer_id", "transaction_date"]].copy()
    activity["activity_month"] = activity["transaction_date"].dt.to_period("M")
    activity["cohort_month"] = activity.groupby("customer_id")["activity_month"].transform("min")
    activity["period"] = (activity["activity_month"] - activity["cohort_month"]).apply(
        lambda value: value.n
    )
    counts = (
        activity.groupby(["cohort_month", "period"])["customer_id"].nunique().unstack(fill_value=0)
    )
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
        previous = set(
            data.loc[
                (data.transaction_date > previous_start) & (data.transaction_date <= current_start),
                "customer_id",
            ]
        )
        current = set(
            data.loc[
                (data.transaction_date > current_start) & (data.transaction_date <= day),
                "customer_id",
            ]
        )
        churned = previous - current
        rows.append(
            {"date": day, "churn_rate": len(churned) / len(previous) * 100 if previous else 0.0}
        )
    return pd.DataFrame(rows, columns=["date", "churn_rate"])
