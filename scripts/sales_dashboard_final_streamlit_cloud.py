import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path


# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide"
)


# --------------------------------------------------
# Load and clean data
# --------------------------------------------------
@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "data" / "online_retail_II.csv"

    sheet1 = pd.read_excel(
        file_path,
        sheet_name="Year 2009-2010"
    )

    sheet2 = pd.read_excel(
        file_path,
        sheet_name="Year 2010-2011"
    )

    df = pd.concat(
        [sheet1, sheet2],
        ignore_index=True
    )

    # Clean data
    df_clean = df[
        (~df["Invoice"].astype(str).str.startswith("C")) &
        (df["Description"].notna()) &
        (df["Price"] > 0) &
        (df["Quantity"] > 0)
    ].copy()

    # Calculate revenue
    df_clean["Revenue"] = (
        df_clean["Quantity"] * df_clean["Price"]
    )

    # Make sure InvoiceDate is a datetime
    df_clean["InvoiceDate"] = pd.to_datetime(
        df_clean["InvoiceDate"]
    )

    return df_clean


df_clean = load_data()


# --------------------------------------------------
# Dashboard title
# --------------------------------------------------
st.title("📊 Online Retail Sales Dashboard")


# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("Filters")

min_date = df_clean["InvoiceDate"].min().date()
max_date = df_clean["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

countries = st.sidebar.multiselect(
    "Country",
    options=sorted(
        df_clean["Country"].dropna().unique()
    ),
    default=[]
)


# --------------------------------------------------
# Apply filters
# --------------------------------------------------
filtered = df_clean.copy()


# Date filter
if len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        (filtered["InvoiceDate"].dt.date >= start_date) &
        (filtered["InvoiceDate"].dt.date <= end_date)
    ]


# Country filter
if countries:
    filtered = filtered[
        filtered["Country"].isin(countries)
    ]


# --------------------------------------------------
# KPIs
# --------------------------------------------------
total_revenue = filtered["Revenue"].sum()
total_orders = filtered["Invoice"].nunique()
unique_customers = filtered["Customer ID"].nunique()

avg_order_value = (
    total_revenue / total_orders
    if total_orders > 0
    else 0
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"£{total_revenue:,.0f}"
)

col2.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col3.metric(
    "Avg Order Value",
    f"£{avg_order_value:,.2f}"
)

col4.metric(
    "Unique Customers",
    f"{unique_customers:,}"
)


# --------------------------------------------------
# Monthly Revenue
# --------------------------------------------------
monthly = (
    filtered
    .set_index("InvoiceDate")
    .resample("ME")["Revenue"]
    .sum()
    .reset_index()
)


fig = px.line(
    monthly,
    x="InvoiceDate",
    y="Revenue",
    title="Monthly Revenue Trend"
)

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue (£)"
)


st.plotly_chart(
    fig,
    width="stretch"
)


# --------------------------------------------------
# Top 10 Products
# --------------------------------------------------
non_product_codes = [
    "POST",
    "DOT",
    "M",
    "C2",
    "BANK CHARGES",
    "CRUK",
    "AMAZONFEE",
    "PADS",
    "DCGS0076"
]


top_products = (
    filtered[
        ~filtered["StockCode"].isin(non_product_codes)
    ]
    .groupby("StockCode")
    .agg(
        total_revenue=("Revenue", "sum"),
        description=("Description", "first")
    )
    .sort_values(
        "total_revenue",
        ascending=False
    )
    .head(10)
    .reset_index()
)


fig_products = px.bar(
    top_products,
    x="total_revenue",
    y="description",
    orientation="h",
    title="Top 10 Products by Revenue"
)

fig_products.update_layout(
    xaxis_title="Revenue (£)",
    yaxis_title="",
    yaxis={
        "categoryorder": "total ascending"
    }
)


# --------------------------------------------------
# Revenue Share by Country
# --------------------------------------------------
country_revenue = (
    filtered
    .groupby("Country")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)


top5 = country_revenue.head(5)
other_total = country_revenue.iloc[5:].sum()


# Only add "Other" when there are more than 5 countries
if len(country_revenue) > 5:
    donut_data = pd.concat(
        [
            top5,
            pd.Series({"Other": other_total})
        ]
    )
else:
    donut_data = top5


fig_countries = px.pie(
    values=donut_data.values,
    names=donut_data.index,
    title="Revenue Share by Country (Top 5 + Other)",
    hole=0.5
)


# --------------------------------------------------
# Business Insights
# --------------------------------------------------
def generate_insights(
    filtered,
    monthly,
    country_revenue
):
    insights = []

    # ----------------------------------------------
    # Insight 1: Month-over-month revenue growth
    # ----------------------------------------------
    if len(monthly) >= 2:
        last_month_revenue = monthly["Revenue"].iloc[-1]
        prev_month_revenue = monthly["Revenue"].iloc[-2]

        if prev_month_revenue > 0:
            growth_pct = (
                (
                    last_month_revenue -
                    prev_month_revenue
                )
                / prev_month_revenue
                * 100
            )

            direction = (
                "grew"
                if growth_pct >= 0
                else "declined"
            )

            insights.append(
                f"📈 Revenue {direction} by "
                f"**{abs(growth_pct):.1f}%** "
                f"in the most recent month compared "
                f"to the previous one."
            )

    # ----------------------------------------------
    # Insight 2: Top market concentration
    # ----------------------------------------------
    total_filtered_revenue = filtered["Revenue"].sum()

    if (
        len(country_revenue) > 0
        and total_filtered_revenue > 0
    ):
        top_country = country_revenue.index[0]

        top_country_share = (
            country_revenue.iloc[0]
            / total_filtered_revenue
            * 100
        )

        insights.append(
            f"🌍 **{top_country}** is the top market, "
            f"accounting for **{top_country_share:.1f}%** "
            f"of total revenue in the current selection."
        )

    # ----------------------------------------------
    # Insight 3: Top product by revenue
    # ----------------------------------------------
    non_product_codes = [
        "POST",
        "DOT",
        "M",
        "C2",
        "BANK CHARGES",
        "CRUK",
        "AMAZONFEE",
        "PADS",
        "DCGS0076"
    ]

    product_revenue = (
        filtered[
            ~filtered["StockCode"].isin(
                non_product_codes
            )
        ]
        .groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    if len(product_revenue) > 0:
        top_product = product_revenue.index[0]
        top_product_revenue = product_revenue.iloc[0]

        insights.append(
            f"🏆 **{top_product}** is the top product "
            f"by revenue, generating "
            f"**£{top_product_revenue:,.0f}**."
        )

    # ----------------------------------------------
    # Insight 4: Average order value
    # ----------------------------------------------
    total_orders = filtered["Invoice"].nunique()

    if total_orders > 0:
        aov = (
            filtered["Revenue"].sum()
            / total_orders
        )

        insights.append(
            f"🛒 The average order value in this "
            f"selection is **£{aov:,.2f}** across "
            f"**{total_orders:,}** orders."
        )

    return insights


# --------------------------------------------------
# Display Business Insights
# --------------------------------------------------
st.subheader("Business Insights")

insights = generate_insights(
    filtered,
    monthly,
    country_revenue
)

if insights:
    for insight in insights:
        st.markdown(f"- {insight}")
else:
    st.info(
        "No data available for the current filter selection."
    )


# --------------------------------------------------
# Display charts side by side
# --------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

chart_col1.plotly_chart(
    fig_products,
    width="stretch"
)

chart_col2.plotly_chart(
    fig_countries,
    width="stretch"
)