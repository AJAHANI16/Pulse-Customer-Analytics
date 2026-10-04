"""Interactive customer analytics dashboard."""

from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_dashboard.etl import run_pipeline
from analytics_dashboard.metrics import (
    cohort_retention,
    customer_segments,
    monthly_revenue,
    rolling_churn,
)

st.set_page_config(page_title="Pulse Analytics", page_icon="📊", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"] {background: #f5f7fb;}
[data-testid="stMetric"] {background: white; border: 1px solid #e3e8ef; padding: 18px; border-radius: 12px;}
h1, h2, h3 {color: #17233d;}
</style>""", unsafe_allow_html=True)

st.title("Pulse Customer Analytics")
st.caption("Revenue, retention, churn, and customer intelligence in one view")

@st.cache_data
def load_default() -> tuple[pd.DataFrame, dict]:
    clean, report = run_pipeline(["data/raw/transactions.csv", "data/raw/transactions.json"], "data/processed")
    return clean, report.to_dict()

uploaded = st.sidebar.file_uploader("Upload CSV or JSON", type=["csv", "json"])
if uploaded:
    suffix = Path(uploaded.name).suffix
    temporary = Path("data/processed") / f"upload{suffix}"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(uploaded.getvalue())
    data, audit = run_pipeline([temporary], "data/processed")
    audit = audit.to_dict()
else:
    data, audit = load_default()

st.sidebar.header("Filters")
min_date, max_date = data.transaction_date.min().date(), data.transaction_date.max().date()
dates = st.sidebar.date_input("Transaction dates", (min_date, max_date), min_value=min_date, max_value=max_date)
countries = st.sidebar.multiselect("Country", sorted(data.country.unique()), default=sorted(data.country.unique()))
channels = st.sidebar.multiselect("Channel", sorted(data.acquisition_channel.unique()), default=sorted(data.acquisition_channel.unique()))
if len(dates) == 2:
    start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1]) + timedelta(days=1)
    data = data[(data.transaction_date >= start) & (data.transaction_date < end)]
data = data[data.country.isin(countries) & data.acquisition_channel.isin(channels)]

if data.empty:
    st.warning("No transactions match these filters.")
    st.stop()

customers = data.customer_id.nunique()
revenue = data.revenue.sum()
aov = data.revenue.mean()
repeat_rate = (data.groupby("customer_id").size().gt(1).mean() * 100)
cols = st.columns(4)
cols[0].metric("Revenue", f"${revenue:,.0f}")
cols[1].metric("Customers", f"{customers:,}")
cols[2].metric("Avg. order value", f"${aov:,.2f}")
cols[3].metric("Repeat customer rate", f"{repeat_rate:.1f}%")

revenue_data = monthly_revenue(data)
left, right = st.columns((2, 1))
with left:
    st.subheader("Revenue trend")
    st.plotly_chart(px.area(revenue_data, x="month", y="revenue", markers=True, color_discrete_sequence=["#5b5ce2"]).update_layout(yaxis_tickprefix="$"), width="stretch")
with right:
    st.subheader("Revenue by channel")
    channel_data = data.groupby("acquisition_channel", as_index=False).revenue.sum()
    channel_chart = px.pie(
        channel_data,
        names="acquisition_channel",
        values="revenue",
        hole=0.62,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(channel_chart, width="stretch")

segments = customer_segments(data)
churn = rolling_churn(data)
tab1, tab2, tab3 = st.tabs(["Retention", "Churn", "Segments"])
with tab1:
    retention = cohort_retention(data)
    st.plotly_chart(px.imshow(retention, text_auto=".0f", aspect="auto", color_continuous_scale="Purples", labels={"color": "Retention %", "x": "Months since signup", "y": "Cohort"}), width="stretch")
with tab2:
    st.plotly_chart(px.line(churn, x="date", y="churn_rate", labels={"churn_rate": "Rolling churn (%)"}, color_discrete_sequence=["#ef6c78"]), width="stretch")
with tab3:
    summary = segments.groupby("segment", observed=True, as_index=False).agg(customers=("customer_id", "nunique"), revenue=("monetary", "sum"))
    st.plotly_chart(px.bar(summary, x="segment", y="customers", color="segment", text_auto=True, color_discrete_sequence=px.colors.qualitative.Set2), width="stretch")
    st.dataframe(segments[["customer_id", "segment", "recency_days", "frequency", "monetary"]].sort_values("monetary", ascending=False), width="stretch", hide_index=True)

with st.expander("Data quality & pipeline audit"):
    st.json(audit)
    st.download_button("Download cleaned data", data.to_csv(index=False), "cleaned_transactions.csv", "text/csv")
