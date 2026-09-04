"""
==============================================================================
NASSAU CANDY - PRODUCT PROFITABILITY AND MARGIN PERFORMANCE DASHBOARD
==============================================================================

WHAT THIS FILE IS
------------------
This is a Streamlit web app. Streamlit turns a plain Python script into an
interactive website. Every time a user moves a slider or picks a filter,
Streamlit re-runs this whole script top to bottom with the new values and
redraws the page. That is the main thing to understand as a beginner: there
is no separate backend, this script IS the app, and it runs again on every
click.

HOW THIS FILE IS ORGANIZED (read it in this order)
----------------------------------------------------
1. Imports and page setup
2. Data loading and cleaning (same logic as the analysis notebook)
3. Key Performance Indicator (KPI) calculations
4. Sidebar filters (date range, division, margin threshold, product search)
5. Four dashboard tabs, one per required module:
      - Product Profitability Overview
      - Division Performance Dashboard
      - Cost vs Margin Diagnostics
      - Profit Concentration Analysis

KPI DEFINITIONS (as specified)
-------------------------------
Gross Margin %        : Gross Profit / Sales
Profit per Unit        : Gross Profit / Units
Revenue Contribution   : Product sales / total sales
Profit Contribution    : Product profit / total profit
Margin Volatility      : Variability (standard deviation) of margin over time

HOW TO RUN THIS APP
--------------------
1. Put this file (app.py) and your data file in the same folder.
2. Install the libraries you need (only once):
       pip install streamlit pandas numpy plotly
3. From a terminal, inside that folder, run:
       streamlit run app.py
4. A browser tab opens automatically at http://localhost:8501

==============================================================================
"""

# ------------------------------------------------------------------------
# STEP 1: IMPORT THE LIBRARIES WE NEED
# ------------------------------------------------------------------------
# streamlit       : builds the actual web page (buttons, sliders, charts, text)
# pandas          : loads and manipulates the data table (same as the notebook)
# numpy           : used for the same flagging logic as the notebook
# plotly.express  : makes interactive charts (hover tooltips, zoom, etc.)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# st.set_page_config must be the first Streamlit command in the script.
# It controls the browser tab title and the page layout.
st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    layout="wide",  # "wide" uses the full browser width instead of a narrow column
)

# Change this to match your CSV's exact filename and location.
DATA_FILE = "Nassau Candy Distributor dataset.csv"


# ------------------------------------------------------------------------
# STEP 2: LOAD AND CLEAN THE DATA
# ------------------------------------------------------------------------
# @st.cache_data tells Streamlit: run this function once, remember the
# result, and reuse it instead of re-loading and re-cleaning the CSV every
# time the user touches a filter. Without this, the app would re-read the
# whole CSV file on every click, which is slow.
@st.cache_data
def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """
    Reads the raw sales CSV and applies the same cleaning steps as the
    analysis notebook (Section 1: Data Cleaning and Validation), so the
    numbers in this dashboard match the notebook.
    """
    df = pd.read_csv(file_path)

    # Remove rows with impossible Sales/Cost/Profit values.
    df = df[(df["Sales"] > 0) & (df["Cost"] >= 0)]
    df = df[df["Sales"] != 0]
    df = df[df["Gross Profit"] <= df["Sales"]]

    # Fill missing Units with the median (robust to outliers).
    df["Units"] = df["Units"].fillna(df["Units"].median())

    # Standardize text so "Chocolate" and " chocolate" are not treated as
    # two different categories.
    df["Division"] = df["Division"].str.strip().str.title()
    df["Product Name"] = df["Product Name"].str.strip().str.title()

    # Convert date columns from text into real dates so we can filter by
    # date range later.
    # NOTE ON DATE FORMATS: different CSV exports write dates differently
    # (for example "13-01-2024" is day first: 13 Jan 2024, since 13 cannot
    # be a month number). dayfirst=True tells pandas to assume DD-MM-YYYY.
    # format="mixed" lets pandas figure out each row's format individually,
    # in case the file has some inconsistency. errors="coerce" turns any
    # date pandas truly cannot parse into a missing value instead of
    # crashing the app.
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, format="mixed", errors="coerce")
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, format="mixed", errors="coerce")

    # Drop any rows where the date genuinely failed to parse, so the date
    # filter below never crashes on a missing or garbled date.
    df = df[df["Order Date"].notna()]

    # Order-line level Gross Margin %, used throughout the app.
    df["Gross Margin %"] = ((df["Gross Profit"] / df["Sales"]) * 100).round(2)

    return df


try:
    df = load_and_clean_data(DATA_FILE)
except FileNotFoundError:
    st.error(
        f"Could not find '{DATA_FILE}'. Place your data file in the same "
        "folder as this app, or update the DATA_FILE variable near the top "
        "of app.py to match your file's name."
    )
    st.stop()  # st.stop() halts the script here so nothing below tries to run on empty data


# ------------------------------------------------------------------------
# STEP 3: SIDEBAR FILTERS (the "User Capabilities" from the spec)
# ------------------------------------------------------------------------
# Everything the user picks here gets applied to a copy of df called
# "filtered_df". The original df is never overwritten, so filters can be
# changed and un-changed without ever needing to reload the CSV.
st.sidebar.title("Nassau Candy Dashboard")
st.sidebar.header("Filters")

# Date range selector.
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
# date_input returns a single date until the user picks a second one.
# This guard avoids a crash during that in-between moment.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Division filter.
all_divisions = sorted(df["Division"].unique())
selected_divisions = st.sidebar.multiselect(
    "Division", options=all_divisions, default=all_divisions
)

# Margin threshold slider.
margin_threshold = st.sidebar.slider(
    "Minimum Gross Margin %",
    min_value=float(df["Gross Margin %"].min()),
    max_value=float(df["Gross Margin %"].max()),
    value=float(df["Gross Margin %"].min()),
    step=1.0,
)

# Product search.
product_search = st.sidebar.text_input("Search product name")

# Apply every filter to build filtered_df.
filtered_df = df[
    (df["Order Date"].dt.date >= start_date)
    & (df["Order Date"].dt.date <= end_date)
    & (df["Division"].isin(selected_divisions))
    & (df["Gross Margin %"] >= margin_threshold)
]
if product_search:
    # case=False makes the search not case-sensitive; na=False ignores blanks.
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(product_search, case=False, na=False)
    ]

st.sidebar.caption(f"{len(filtered_df):,} of {len(df):,} order lines match your filters.")

if filtered_df.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()


# ------------------------------------------------------------------------
# STEP 4: BUILD THE SUMMARY TABLES AND THE FIVE KPIs
# ------------------------------------------------------------------------
# These are recalculated on filtered_df every time filters change, which is
# what makes every tab below stay in sync with the sidebar.

def build_product_summary(data: pd.DataFrame) -> pd.DataFrame:
    """
    One row per product, with all five required KPIs plus a risk flag used
    in the Cost vs Margin Diagnostics tab.
    """
    total_sales = data["Sales"].sum()
    total_profit = data["Gross Profit"].sum()

    summary = data.groupby("Product Name").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
    ).reset_index()

    # KPI 1: Gross Margin % = Gross Profit / Sales, at the product level.
    summary["Gross_Margin_Percent"] = (summary["Total_Profit"] / summary["Total_Sales"] * 100).round(2)

    # KPI 2: Profit per Unit = Gross Profit / Units.
    summary["Profit_per_Unit"] = (summary["Total_Profit"] / summary["Total_Units"]).round(2)

    # KPI 3: Revenue Contribution = product sales / total sales.
    summary["Revenue_Contribution_%"] = (summary["Total_Sales"] / total_sales * 100).round(2)

    # KPI 4: Profit Contribution = product profit / total profit.
    summary["Profit_Contribution_%"] = (summary["Total_Profit"] / total_profit * 100).round(2)

    # KPI 5: Margin Volatility = variability of margin over time.
    # For each product, this is the standard deviation of its order-line
    # Gross Margin % across all its orders. A higher number means the
    # product's margin swings around more from order to order.
    volatility = data.groupby("Product Name")["Gross Margin %"].std().round(2)
    summary["Margin_Volatility"] = summary["Product Name"].map(volatility).fillna(0)

    # Risk flag, used in the Cost vs Margin Diagnostics tab.
    sales_median = summary["Total_Sales"].median()
    margin_median = summary["Gross_Margin_Percent"].median()

    def flag_risk(row):
        if row["Total_Profit"] < 0:
            return "Discontinuation Review"
        elif row["Gross_Margin_Percent"] < margin_median and row["Total_Sales"] > sales_median:
            return "Repricing Candidate"
        elif row["Gross_Margin_Percent"] < margin_median:
            return "Cost Renegotiation"
        else:
            return "Healthy"

    summary["Risk_Flag"] = summary.apply(flag_risk, axis=1)
    return summary


def build_division_summary(data: pd.DataFrame) -> pd.DataFrame:
    """One row per division, using the same KPI definitions as the product summary."""
    total_sales = data["Sales"].sum()
    total_profit = data["Gross Profit"].sum()

    summary = data.groupby("Division").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
    ).reset_index()

    summary["Gross_Margin_Percent"] = (summary["Total_Profit"] / summary["Total_Sales"] * 100).round(2)
    summary["Profit_per_Unit"] = (summary["Total_Profit"] / summary["Total_Units"]).round(2)
    summary["Revenue_Contribution_%"] = (summary["Total_Sales"] / total_sales * 100).round(2)
    summary["Profit_Contribution_%"] = (summary["Total_Profit"] / total_profit * 100).round(2)

    volatility = data.groupby("Division")["Gross Margin %"].std().round(2)
    summary["Margin_Volatility"] = summary["Division"].map(volatility).fillna(0)

    company_avg_margin = data["Gross Margin %"].mean()
    summary["Performance_Flag"] = np.where(
        summary["Gross_Margin_Percent"] >= company_avg_margin,
        "Strong Efficiency",
        "Structural Margin Issue",
    )
    return summary


def build_pareto(product_summary: pd.DataFrame) -> pd.DataFrame:
    """Sorts products by profit and adds a running (cumulative) percent of
    total profit. This is what powers the Pareto (80/20) chart."""
    pareto = product_summary.sort_values("Total_Profit", ascending=False).reset_index(drop=True)
    pareto["Cumulative_Profit"] = pareto["Total_Profit"].cumsum()
    pareto["Cumulative_Profit_%"] = (pareto["Cumulative_Profit"] / pareto["Total_Profit"].sum() * 100).round(2)
    return pareto


product_summary = build_product_summary(filtered_df)
division_summary = build_division_summary(filtered_df)
pareto = build_pareto(product_summary)


# ------------------------------------------------------------------------
# STEP 5: PAGE HEADER AND OVERALL KPI ROW
# ------------------------------------------------------------------------
st.title("Nassau Candy: Product Profitability and Margin Performance")
st.caption("Filters applied from the sidebar update every chart and table below.")

# KPI 1: Gross Margin % for the current filtered selection.
overall_gross_margin = filtered_df["Gross Profit"].sum() / filtered_df["Sales"].sum() * 100

# KPI 2: Profit per Unit for the current filtered selection.
overall_profit_per_unit = filtered_df["Gross Profit"].sum() / filtered_df["Units"].sum()

# KPI 3: Revenue Contribution = the filtered selection's sales divided by
# total sales across the WHOLE dataset (before any filters). This shows
# what share of total company revenue the current filter selection covers.
overall_revenue_contribution = filtered_df["Sales"].sum() / df["Sales"].sum() * 100

# KPI 4: Profit Contribution = the filtered selection's profit divided by
# total profit across the WHOLE dataset, same idea as Revenue Contribution.
overall_profit_contribution = filtered_df["Gross Profit"].sum() / df["Gross Profit"].sum() * 100

# KPI 5: Margin Volatility = standard deviation of order-level Gross Margin %
# for the current filtered selection.
overall_margin_volatility = filtered_df["Gross Margin %"].std()

# st.columns() puts these numbers side by side instead of stacked.
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Gross Margin %", f"{overall_gross_margin:.1f}%")
kpi2.metric("Profit per Unit", f"${overall_profit_per_unit:,.2f}")
kpi3.metric("Revenue Contribution", f"{overall_revenue_contribution:.1f}%")
kpi4.metric("Profit Contribution", f"{overall_profit_contribution:.1f}%")
kpi5.metric("Margin Volatility", f"{overall_margin_volatility:.2f}")

st.caption(
    "Revenue Contribution and Profit Contribution above compare the current "
    "filtered selection to the full unfiltered dataset. Per-product and "
    "per-division versions of all five KPIs are shown in the tables below."
)

st.divider()

# st.tabs() creates the four clickable tabs, one per required dashboard module.
tab1, tab2, tab3, tab4 = st.tabs([
    "Product Profitability Overview",
    "Division Performance Dashboard",
    "Cost vs Margin Diagnostics",
    "Profit Concentration Analysis",
])


# ------------------------------------------------------------------------
# TAB 1: PRODUCT PROFITABILITY OVERVIEW
#   - Product-level margin leaderboard
#   - Profit contribution charts
# ------------------------------------------------------------------------
with tab1:
    st.subheader("Product-Level Margin Leaderboard")
    st.caption("Ranked by Gross Margin %. All five KPIs are shown per product.")

    leaderboard = product_summary.sort_values("Gross_Margin_Percent", ascending=False)
    st.dataframe(
        leaderboard[[
            "Product Name",
            "Gross_Margin_Percent",
            "Profit_per_Unit",
            "Revenue_Contribution_%",
            "Profit_Contribution_%",
            "Margin_Volatility",
            "Total_Sales",
            "Total_Profit",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Profit Contribution by Product")
    st.caption("Top 15 products by Profit Contribution %.")

    top15 = product_summary.sort_values("Profit_Contribution_%", ascending=False).head(15)
    fig_profit = px.bar(
        top15,
        x="Profit_Contribution_%",
        y="Product Name",
        orientation="h",
        color="Gross_Margin_Percent",
        color_continuous_scale="RdYlGn",
        labels={"Profit_Contribution_%": "Profit Contribution (%)", "Gross_Margin_Percent": "Gross Margin %"},
    )
    # Plotly draws bars bottom to top by default; flip so the top product is on top.
    fig_profit.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_profit, use_container_width=True)


# ------------------------------------------------------------------------
# TAB 2: DIVISION PERFORMANCE DASHBOARD
#   - Revenue vs profit comparison
#   - Margin distribution by division
# ------------------------------------------------------------------------
with tab2:
    st.subheader("Revenue vs Profit by Division")
    st.caption("A division whose profit bar is much shorter than its revenue bar has a margin problem.")

    # "melt" reshapes the table from wide (separate Sales/Profit columns) to
    # long (one Metric column and one Value column). This is the shape
    # px.bar needs to draw grouped bars side by side.
    division_long = division_summary.melt(
        id_vars="Division",
        value_vars=["Total_Sales", "Total_Profit"],
        var_name="Metric",
        value_name="Value",
    )
    fig_div = px.bar(
        division_long, x="Division", y="Value", color="Metric", barmode="group",
    )
    st.plotly_chart(fig_div, use_container_width=True)

    st.subheader("Margin Distribution by Division")
    st.caption("Each box shows the spread of order-level margins within a division. A wide box means inconsistent pricing.")
    fig_box = px.box(filtered_df, x="Division", y="Gross Margin %", color="Division")
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Division Summary Table")
    st.dataframe(
        division_summary[[
            "Division",
            "Gross_Margin_Percent",
            "Profit_per_Unit",
            "Revenue_Contribution_%",
            "Profit_Contribution_%",
            "Margin_Volatility",
            "Performance_Flag",
        ]],
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------------------
# TAB 3: COST VS MARGIN DIAGNOSTICS
#   - Cost-sales scatter plots
#   - Margin risk flags
# ------------------------------------------------------------------------
with tab3:
    st.subheader("Cost vs Sales by Product")
    st.caption(
        "Each dot is a product. Color shows Gross Margin %. "
        "Size shows units sold."
    )

    product_cost = filtered_df.groupby("Product Name")["Cost"].sum().reset_index()
    scatter_data = product_summary.merge(product_cost, on="Product Name", how="left")

    fig_scatter = px.scatter(
        scatter_data,
        x="Cost",
        y="Total_Sales",
        color="Gross_Margin_Percent",
        size="Total_Units",
        hover_name="Product Name",
        color_continuous_scale="RdYlGn",
        labels={"Cost": "Total Cost ($)", "Total_Sales": "Total Sales ($)"},
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Margin Risk Flags")
    st.caption("Negative profit, thin margin at high volume, or thin margin generally.")

    flag_counts = product_summary["Risk_Flag"].value_counts().reset_index()
    flag_counts.columns = ["Risk_Flag", "Count"]
    fig_flags = px.bar(flag_counts, x="Risk_Flag", y="Count", color="Risk_Flag")
    st.plotly_chart(fig_flags, use_container_width=True)

    flag_choice = st.selectbox("Show products flagged as:", flag_counts["Risk_Flag"])
    st.dataframe(
        product_summary[product_summary["Risk_Flag"] == flag_choice],
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------------------
# TAB 4: PROFIT CONCENTRATION ANALYSIS
#   - Pareto charts
#   - Dependency indicators
# ------------------------------------------------------------------------
with tab4:
    st.subheader("Pareto Analysis: Profit Concentration")

    products_for_80pct = pareto[pareto["Cumulative_Profit_%"] <= 80].shape[0]
    pct_of_lineup = round(products_for_80pct / len(pareto) * 100, 1) if len(pareto) else 0
    st.info(
        f"{products_for_80pct} products generate 80% of total profit. "
        f"That is {pct_of_lineup}% of the {len(pareto)}-product lineup shown."
    )

    # A combo chart: bars for each product's own profit, a line for the
    # running cumulative percent. This is the standard Pareto chart shape.
    fig_pareto = px.bar(
        pareto, x="Product Name", y="Total_Profit", labels={"Total_Profit": "Total Profit ($)"},
    )
    fig_pareto.add_scatter(
        x=pareto["Product Name"],
        y=pareto["Cumulative_Profit_%"],
        mode="lines+markers",
        name="Cumulative Profit %",
        yaxis="y2",
    )
    fig_pareto.update_layout(
        yaxis2=dict(title="Cumulative Profit %", overlaying="y", side="right", range=[0, 100]),
        xaxis=dict(showticklabels=False),  # too many product names to show at once
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    st.subheader("Regional Dependency Indicator")
    st.caption("A single region driving most of your sales is a concentration risk.")

    if "Region" in filtered_df.columns:
        region_summary = filtered_df.groupby("Region").agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Gross Profit", "sum"),
        ).reset_index().sort_values("Total_Sales", ascending=False)
        region_summary["Sales_Share_%"] = (
            region_summary["Total_Sales"] / region_summary["Total_Sales"].sum() * 100
        ).round(2)

        fig_region = px.pie(
            region_summary, names="Region", values="Total_Sales", hole=0.45,
        )
        st.plotly_chart(fig_region, use_container_width=True)
        st.dataframe(region_summary, use_container_width=True, hide_index=True)
    else:
        st.caption("No 'Region' column found in this dataset. Skipping regional breakdown.")
