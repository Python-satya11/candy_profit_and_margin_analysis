# Nassau Candy Distributor - Profitability & Margin Analysis

## Project Overview

This project presents an exploratory data analysis (EDA) of the **Nassau Candy Distributor** product-line dataset. The objective is to understand sales, cost, gross profit, gross margin, product performance, division performance, regional distribution, and profit concentration, and to turn those findings into practical business insights.

The analysis was performed using **Python, Pandas, NumPy, Matplotlib, Seaborn, and Jupyter Notebook**.

---

## 1. Problem Statement

Sales revenue alone does not provide a complete picture of product performance. A product may generate high sales while producing a low margin, while another product may have a high margin but contribute little total profit because its sales volume is small.

The main problem addressed in this project is:

> **How can the Nassau Candy Distributor dataset be explored and transformed into meaningful profitability insights that identify strong products, weak products, margin issues, and areas where management should focus pricing, cost control, inventory, and product strategy?**

The EDA addresses the following business questions:

- Which products generate the highest total gross profit?
- Which products have the strongest gross margins?
- Which products combine high sales with low margins?
- Which products need pricing or cost attention?
- Which divisions contribute most of the company's revenue and profit?
- How concentrated are revenue and profit across products?
- What regional sales concentration exists?
- What data quality issues must be addressed before profitability analysis?

---

## 2. Dataset Description

The dataset contains **10,194 records and 18 original columns**. It includes order information, customer and geographic information, product information, and financial measures such as Sales, Units, Gross Profit, and Cost.

The original fields cover:

- Order and customer identification
- Order and shipping dates
- Shipping method
- Country, city, state/province, and postal code
- Division and region
- Product identification and product name
- Sales, units, gross profit, and cost

### Column Dictionary

The complete explanation of the dataset columns is maintained separately.

**[View the Column Dictionary](
data_dictionary.md)**

---

## 3. Dataset Inspection and Exploratory Analysis

### 3.1 Dataset Structure and Data Types

The first inspection used `df.info()` and `df.describe()` to understand the dataset structure and numeric variables.

The dataset contains:

- **10,194 rows**
- **18 original columns**
- **3 floating-point financial columns:** Sales, Gross Profit, Cost
- **3 integer columns:** Row ID, Customer ID, Units
- **12 text/string columns**

All 10,194 records were reported as non-null during the initial structure check.

The Order Date and Ship Date fields were initially stored as text and were later converted to proper datetime values.

### 3.2 Numeric Distribution

Summary statistics were used to examine the minimum, maximum, mean, standard deviation, and quartiles of the major numeric fields.

| Variable | Mean | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| Sales | 13.91 | 1.25 | 10.80 | 260.00 |
| Units | 3.79 | 1.00 | 3.00 | 14.00 |
| Gross Profit | 9.17 | 0.25 | 7.47 | 130.00 |
| Cost | 4.74 | 0.60 | 3.60 | 130.00 |

The maximum values are substantially higher than the means and medians, indicating comparatively extreme observations in the numeric data. These observations should be considered during further analysis and visualization.

The notebook performs business-rule validation, but it does **not** apply a formal statistical outlier test such as IQR or z-score to every numeric variable. Therefore, the presence of extreme values should not automatically be interpreted as confirmed statistical outliers.

### 3.3 Categorical Consistency and Anomalies

Categorical fields such as **Division** and **Product Name** were inspected for formatting inconsistencies.

The cleaning process specifically addressed:

- Leading or trailing spaces
- Inconsistent capitalization
- Text formatting that could cause the same category to be treated as multiple categories

For example, `"Chocolate"` and `" chocolate "` could otherwise be counted as different values during grouping.

The notebook standardizes these values before product and division aggregation.

No unsupported claim is made that every possible categorical anomaly was identified; the documented work focuses on formatting consistency.

### 3.4 Division Distribution

Division-level analysis showed a strong concentration in the Chocolate division:

| Division | Total Sales | Total Profit | Avg. Margin % | Revenue Share | Profit Share |
|---|---:|---:|---:|---:|---:|
| Chocolate | $131,692.90 | $88,824.62 | 67.46% | 92.88% | 95.06% |
| Other | $9,663.25 | $4,333.45 | 37.67% | 6.82% | 4.64% |
| Sugar | $427.48 | $284.73 | 57.69% | 0.30% | 0.30% |

This distribution shows that Chocolate is the primary contributor to both revenue and gross profit.

---

## 4. Data Cleaning Methods

The notebook follows a structured data cleaning and validation process.

### 4.1 Inspect Structure and Summary Statistics

The analysis starts with:

```python
df.info()
df.describe()
```

These functions are used to inspect column names, data types, non-null counts, and numeric summary statistics.

### 4.2 Validate Sales and Cost

Records with negative Sales or negative Cost are removed:

```python
df = df[(df["Sales"] > 0) & (df["Cost"] >= 0)]
```

The purpose is to prevent invalid financial values from affecting profitability calculations.

### 4.3 Remove Zero-Sales Records

Zero-sales records are removed:

```python
df = df[df["Sales"] != 0]
```

This keeps the profitability analysis focused on actual sales transactions.

### 4.4 Validate Gross Profit

Rows where Gross Profit exceeds Sales are removed:

```python
df = df[df["Gross Profit"] <= df["Sales"]]
```

The business rule used in the analysis is:

```text
Gross Profit = Sales - Cost
```

Therefore, Gross Profit should not be greater than Sales.

### 4.5 Check Missing Unit Values

The notebook checks the number of missing Unit values:

```python
df["Units"].isnull().sum()
```

The result was **0 missing values**.

The notebook also contains a median-imputation approach:

```python
df["Units"] = df["Units"].fillna(df["Units"].median())
```

Because there were no missing Unit values, this imputation was not required in the reported dataset.

### 4.6 Standardize Text Fields

Division and Product Name values are cleaned using:

```python
df["Division"] = df["Division"].str.strip().str.title()
df["Product Name"] = df["Product Name"].str.strip().str.title()
```

This removes unwanted spaces and standardizes capitalization.

### 4.7 Convert Date Fields

The date columns are converted from text into datetime values:

```python
df["Order Date"] = pd.to_datetime(
    df["Order Date"], format="%d-%m-%Y"
)

df["Ship Date"] = pd.to_datetime(
    df["Ship Date"], format="%d-%m-%Y"
)
```

This makes the dates suitable for sorting, filtering, date differences, and future time-series analysis.

---

## 5. Feature Engineering

Feature engineering creates additional variables that make the raw dataset more useful for profitability analysis.

### 5.1 Gross Margin %

Gross Margin % measures the proportion of sales that remains as gross profit.

**Formula:**

```text
Gross Margin % = (Gross Profit / Sales) × 100
```

Python implementation:

```python
df["Gross Margin %"] = (
    df["Gross Profit"] / df["Sales"]
) * 100
```

This makes it possible to compare profitability efficiency across products with different sales levels.

### 5.2 Profit per Unit

Profit per Unit measures gross profit generated from each unit sold.

**Formula:**

```text
Profit per Unit = Gross Profit / Units
```

Python implementation:

```python
df["Profit per Unit"] = (
    df["Gross Profit"] / df["Units"]
)
```

This metric helps identify products that generate more profit from each item sold.

### 5.3 Product-Level Aggregation

Products were summarized using:

- Total Sales
- Total Gross Profit
- Total Units
- Average Gross Margin %

This summary supports product comparison and ranking.

### 5.4 Profit and Margin Ranking

Products were ranked separately by:

- **Profit Rank:** based on total gross profit
- **Margin Rank:** based on average gross margin percentage

A product can therefore rank highly in total profit while not having the highest margin, which is an important distinction for business decision-making.

### 5.5 Product Performance Categories

Median values were used as practical thresholds to classify products into:

**Star Products**
- Above-median total profit
- Above-median average margin

**Volume Traps**
- Above-median sales
- Below-median average margin

**Underperformers**
- Below-median sales
- Below-median total profit

The analysis identified:

- **5 star products**
- **2 volume traps**
- **6 underperformers**

### 5.6 Action Flags

Each product was assigned an action category based on the documented decision logic:

- Healthy
- Cost Renegotiation
- Repricing Candidate
- Discontinuation Review

The results were:

| Action | Number of Products |
|---|---:|
| Healthy | 8 |
| Cost Renegotiation | 5 |
| Repricing Candidate | 2 |
| Discontinuation Review | 0 |

---

## 6. Key Findings from EDA

### Product Profitability

The leading total profit contributors were:

1. **Wonka Bar - Scrumdiddlyumptious** - $19,357.50
2. **Wonka Bar - Triple Dazzle Caramel** - $18,610.20
3. **Wonka Bar - Milk Chocolate** - $17,443.37
4. **Wonka Bar - Nutty Crunch Surprise** - $16,819.95
5. **Wonka Bar - Fudge Mallows** - $16,593.60

### Profit Concentration

The Pareto analysis found that **4 products generate approximately 80% of total profit out of 15 products**, representing about **26.7% of the product line**.

The same four products also generate approximately **80% of total revenue**.

### Regional Distribution

Sales were distributed as follows:

| Region | Sales Share |
|---|---:|
| Pacific | 32.66% |
| Atlantic | 29.06% |
| Interior | 22.60% |
| Gulf | 15.69% |

Pacific had the largest sales share, followed by Atlantic, Interior, and Gulf.

---

## 7. Business Recommendations

1. **Protect the core profit products.** The products responsible for the majority of profit and revenue should receive careful inventory, pricing, and availability management.

2. **Review high-sales, low-margin products.** The two volume traps should be examined for pricing, discounts, supplier costs, and other cost drivers.

3. **Investigate supplier cost opportunities.** Products flagged for cost renegotiation should be reviewed for sourcing, purchasing terms, packaging, and alternative suppliers.

4. **Reduce product concentration risk.** Since a small group of products generates most revenue and profit, developing additional strong contributors could reduce dependence on the current core portfolio.

5. **Investigate weaker divisions.** The Other and Sugar divisions should receive deeper analysis to understand whether their lower margin performance is caused by pricing, product mix, costs, or demand.

---

## 8. Future Analysis

The current EDA provides a descriptive foundation. Possible next steps include:

- Monthly and quarterly sales and profit trends
- Seasonal demand analysis
- Formal outlier detection using IQR or z-score methods
- Correlation analysis among Sales, Cost, Units, Gross Profit, and Profit per Unit
- Customer-level profitability analysis
- Regional product-mix analysis
- Shipment delay analysis using Order Date and Ship Date
- Analysis of discounts, returns, supplier costs, and logistics costs if those fields become available

These extensions would help explain not only **what is happening**, but also **why it is happening**.

---

## 9. Tools and Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Jupyter Notebook
- Streamlit

---

## Author

**Satyaranjan Jena**  
MCA  
Email: *satya.python1999@gmai.com*
