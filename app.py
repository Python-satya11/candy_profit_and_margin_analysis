# Imports
# Streamlit provides the dashboard interface.
# Pandas and NumPy handle data preparation and calculations.
# Plotly Express creates interactive charts.
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configure the page before creating Streamlit elements.
st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    layout="wide",
)
# Load and clean data
# Cache the cleaned dataset to avoid repeating file I/O and data preparation
# when dashboard filters change.
@st.cache_data
def load_and_clean_data(file) -> pd.DataFrame:
    """Load the sales data, clean the required fields, and calculate core metrics."""
    df = pd.read_csv(file)

    # Remove records with invalid sales, cost, or profit values.
    df = df[(df["Sales"] > 0) & (df["Cost"] >= 0)]
    df = df[df["Sales"] != 0]
    df = df[df["Gross Profit"] <= df["Sales"]]

    # Fill missing unit values with the median.
    df["Units"] = df["Units"].fillna(df["Units"].median())

    # Standardize text fields for consistent grouping and filtering.
    df["Division"] = df["Division"].str.strip().str.title()
    df["Product Name"] = df["Product Name"].str.strip().str.title()

    # Convert date fields to datetime and handle inconsistent formats safely.
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, format="mixed", errors="coerce")
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, format="mixed", errors="coerce")

    # Exclude records with invalid order dates.
    df = df[df["Order Date"].notna()]

    # Calculate core profitability metrics.
    df["Gross Margin %"] = ((df["Gross Profit"] / df["Sales"]) * 100).round(2)
    df["Profit per Unit"] = (df["Gross Profit"] / df["Units"]).round(2)

    return df

# Data source
DEFAULT_FILE = "Nassau Candy Distributor dataset.csv"
raw_source = DEFAULT_FILE

try:
    df = load_and_clean_data(raw_source)
except FileNotFoundError:
    st.error(
        f"Could not find '{DEFAULT_FILE}'. Place the data file in the same "
        "folder as this app."
    )
    st.stop()
# Sidebar Filters (The "User Capabilities" From The Spec)
# Apply all selected filters to a separate working DataFrame.
st.sidebar.header("Filters")

# Date range filter
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
# Handle the single-date state returned by date_input.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Division filter
all_divisions = sorted(df["Division"].unique())
selected_divisions = st.sidebar.multiselect(
    "Division", options=all_divisions, default=all_divisions
)

# Gross margin threshold
# Display records meeting the selected minimum gross margin.
margin_threshold = st.sidebar.slider(
    "Minimum Gross Margin %",
    min_value=float(df["Gross Margin %"].min()),
    max_value=float(df["Gross Margin %"].max()),
    value=float(df["Gross Margin %"].min()),
    step=1.0,
)

# Product search
product_search = st.sidebar.text_input("Search product name")

# Apply all filters.
filtered_df = df[
    (df["Order Date"].dt.date >= start_date)
    & (df["Order Date"].dt.date <= end_date)
    & (df["Division"].isin(selected_divisions))
    & (df["Gross Margin %"] >= margin_threshold)
]
if product_search:
    # Use a case-insensitive search and ignore missing product names.
    filtered_df = filtered_df[
        filtered_df["Product Name"].str.contains(product_search, case=False, na=False)
    ]

st.sidebar.caption(f"{len(filtered_df):,} of {len(df):,} order lines match your filters.")

if filtered_df.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()
# Build The Summary Tables (Same Groupby Logic As The Notebook)
# Recalculate summaries whenever the filters change.

def build_product_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return product-level sales, profit, margin, and action indicators."""
    summary = data.groupby("Product Name").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Avg_Margin_Percent=("Gross Margin %", "mean"),
    ).reset_index()
    summary["Avg_Margin_Percent"] = summary["Avg_Margin_Percent"].round(2)

    sales_median = summary["Total_Sales"].median()
    margin_median = summary["Avg_Margin_Percent"].median()

    def flag_action(row):
        if row["Total_Profit"] < 0:
            return "Discontinuation Review"
        elif row["Avg_Margin_Percent"] < margin_median and row["Total_Sales"] > sales_median:
            return "Repricing Candidate"
        elif row["Avg_Margin_Percent"] < margin_median:
            return "Cost Renegotiation"
        else:
            return "Healthy"

    summary["Action_Flag"] = summary.apply(flag_action, axis=1)
    return summary

def build_division_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return division-level sales, profit, margin, and performance indicators."""
    summary = data.groupby("Division").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Avg_Margin_Percent=("Gross Margin %", "mean"),
    ).reset_index()
    summary["Avg_Margin_Percent"] = summary["Avg_Margin_Percent"].round(2)
    summary["Revenue_Share_%"] = (summary["Total_Sales"] / summary["Total_Sales"].sum() * 100).round(2)
    summary["Profit_Share_%"] = (summary["Total_Profit"] / summary["Total_Profit"].sum() * 100).round(2)

    company_avg_margin = data["Gross Margin %"].mean()
    summary["Performance_Flag"] = np.where(
        summary["Avg_Margin_Percent"] >= company_avg_margin,
        "Strong Efficiency",
        "Structural Margin Issue",
    )
    return summary

def build_pareto(product_summary: pd.DataFrame) -> pd.DataFrame:
    """Sort products by profit and calculate cumulative profit share."""
    pareto = product_summary.sort_values("Total_Profit", ascending=False).reset_index(drop=True)
    pareto["Cumulative_Profit"] = pareto["Total_Profit"].cumsum()
    pareto["Cumulative_Profit_%"] = (pareto["Cumulative_Profit"] / pareto["Total_Profit"].sum() * 100).round(2)
    pareto["Product_Rank_%"] = ((pareto.index + 1) / len(pareto) * 100).round(2)
    return pareto

product_summary = build_product_summary(filtered_df)
division_summary = build_division_summary(filtered_df)
pareto = build_pareto(product_summary)
# Page Header + Kpi Row
st.title("Nassau Candy: Product Profitability and Margin Performance")
st.caption("All charts and tables update based on the selected filters.")

# Display the key performance indicators in four columns.
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.0f}")
kpi2.metric("Total Profit", f"${filtered_df['Gross Profit'].sum():,.0f}")
kpi3.metric("Avg Gross Margin %", f"{filtered_df['Gross Margin %'].mean():.1f}%")
kpi4.metric("Products in View", f"{filtered_df['Product Name'].nunique():,}")

st.divider()

# Dashboard sections.
tab1, tab2, tab3, tab4 = st.tabs([
    " Product Profitability Overview",
    " Division Performance Dashboard",
    " Cost vs Margin Diagnostics",
    " Profit Concentration Analysis",
])
# TAB 1: PRODUCT PROFITABILITY OVERVIEW
#   - Product-level margin leaderboard
#   - Profit contribution charts
with tab1:
    st.subheader("Product-Level Margin Leaderboard")
    st.caption("Products are ranked by average gross margin.")

    leaderboard = product_summary.sort_values("Avg_Margin_Percent", ascending=False)
    st.dataframe(
        leaderboard[[
            "Product Name", "Avg_Margin_Percent", "Total_Sales",
            "Total_Profit", "Total_Units", "Action_Flag",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Profit Contribution by Product")
    st.caption("Top 15 products by total gross profit.")

    top15 = product_summary.sort_values("Total_Profit", ascending=False).head(15)
    fig_profit = px.bar(
        top15,
        x="Total_Profit",
        y="Product Name",
        orientation="h",
        color="Avg_Margin_Percent",
        color_continuous_scale="RdYlGn",
        labels={"Total_Profit": "Total Profit ($)", "Avg_Margin_Percent": "Avg Margin %"},
    )
    # Place the highest-profit product at the top of the chart.
    fig_profit.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_profit, use_container_width=True)
# TAB 2: DIVISION PERFORMANCE DASHBOARD
#   - Revenue vs profit comparison
#   - Margin distribution by division
with tab2:
    st.subheader("Revenue vs Profit by Division")
    st.caption("A lower profit contribution relative to sales may indicate a margin issue.")

    # Reshape the summary for grouped comparison.
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
    st.caption("Box plots show the distribution of order-level gross margins by division.")
    fig_box = px.box(filtered_df, x="Division", y="Gross Margin %", color="Division")
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Division Summary Table")
    st.dataframe(division_summary, use_container_width=True, hide_index=True)
# TAB 3: COST VS MARGIN DIAGNOSTICS
#   - Cost-sales scatter plots
#   - Margin risk flags
with tab3:
    st.subheader("Sales vs Profit by Product")
    st.caption(
        "Each point represents a product. The horizontal line marks zero profit; "
        "color represents average margin and size represents units sold."
    )
    fig_scatter = px.scatter(
        product_summary,
        x="Total_Sales",
        y="Total_Profit",
        color="Avg_Margin_Percent",
        size="Total_Units",
        hover_name="Product Name",
        color_continuous_scale="RdYlGn",
        labels={"Total_Sales": "Total Sales ($)", "Total_Profit": "Total Profit ($)"},
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Margin Risk Flags")
    st.caption("Products are grouped by profitability and margin risk.")

    flag_counts = product_summary["Action_Flag"].value_counts().reset_index()
    flag_counts.columns = ["Action_Flag", "Count"]
    fig_flags = px.bar(flag_counts, x="Action_Flag", y="Count", color="Action_Flag")
    st.plotly_chart(fig_flags, use_container_width=True)

    flag_choice = st.selectbox("Show products flagged as:", flag_counts["Action_Flag"])
    st.dataframe(
        product_summary[product_summary["Action_Flag"] == flag_choice],
        use_container_width=True,
        hide_index=True,
    )
# TAB 4: PROFIT CONCENTRATION ANALYSIS
#   - Pareto charts
#   - Dependency indicators
with tab4:
    st.subheader("Pareto Analysis : Profit Concentration")

    products_for_80pct = pareto[pareto["Cumulative_Profit_%"] <= 80].shape[0]
    pct_of_lineup = round(products_for_80pct / len(pareto) * 100, 1) if len(pareto) else 0
    st.info(
        f"**{products_for_80pct} products** generate 80% of total profit : "
        f"which represents **{pct_of_lineup}%** of the {len(pareto)} products in view."
    )

    # Combine product profit bars with cumulative profit share.
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
        xaxis=dict(showticklabels=False),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    st.subheader("Regional Dependency Indicator")
    st.caption("A high sales share from one region may indicate concentration risk.")

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
        st.caption("No 'Region' column found in this dataset : skipping regional breakdown.")
