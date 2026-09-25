# Project Notes — Online Retail Sales Dashboard

Internal documentation of methodology, decisions, and findings. This complements `README.md` (which is the public-facing overview) with the technical detail a reviewer or future-you would want when auditing the analysis.

---

## 1. Project Overview

- **Goal:** Turn raw transactional data into an executive-style sales dashboard, built as a standalone portfolio project.
- **Tools:** Python, Pandas, Plotly, Streamlit.
- **Deliverables:** Cleaned dataset, EDA, KPI calculations, visualizations, an interactive Streamlit dashboard, automated business insights, business recommendations, and a deployed live app.

## 2. Dataset

- **Source:** Online Retail II (UCI Machine Learning Repository, Chen 2012).
- **Description:** Transactions from a UK-based online retailer, December 2009–December 2011. Customer base is mostly wholesale gift-ware buyers rather than individual consumers (reflected in high average order value — see §5).
- **Raw shape:** 1,067,371 rows across two sheets (2009–2010, 2010–2011), stacked into a single DataFrame.
- **Columns:** `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`.

## 3. Data Cleaning

**Rules applied, in order, with rationale:**

| Rule                                                                          | Rationale                                                                                                     |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Exclude `Invoice` starting with `"C"`                                         | These are cancellations — including them would double-count reversed transactions.                            |
| Exclude rows where `Description` is null                                      | These are internal write-offs/adjustments, not real sales (e.g. "damaged", "check", "missing", "found").      |
| Exclude `Price <= 0`                                                          | Zero/negative price rows are adjustments or data errors, not revenue-generating transactions.                 |
| Exclude `Quantity <= 0` (non-cancelled only)                                  | Residual invalid quantity entries not already caught by the cancellation filter.                              |
| Keep missing `Customer ID` for revenue KPIs, exclude from customer-count KPIs | Anonymous/guest-style transactions still represent real revenue but shouldn't be counted as unique customers. |

**Result:** 25,701 rows removed (2.4% of raw data) → **1,041,670 clean rows** used for all downstream analysis.

**Note on rigor:** the excluded rows were investigated before being dropped — e.g. cross-checking that null `Description` lined up with `Price == 0` — rather than applying filters blindly. This is worth calling out in an interview: it shows the cleaning rules were evidence-based, not assumed.

## 4. Feature Engineering

- `Revenue = Quantity × Price`, calculated at the transaction-line level after cleaning.
- `InvoiceDate` converted to datetime for resampling.

## 5. KPI Results

| KPI                 | Value                                  |
| ------------------- | -------------------------------------- |
| Total Revenue       | £20,972,594.57                         |
| Total Orders        | 40,077                                 |
| Average Order Value | £523.31                                |
| Unique Customers    | 5,878                                  |
| Top Product         | Regency Cakestand 3 Tier (£344,563.25) |
| Top Market          | United Kingdom (~85% of revenue)       |

Non-product `StockCode`s (`POST`, `DOT`, `M`, `C2`, `BANK CHARGES`, `CRUK`, `AMAZONFEE`, `PADS`, `DCGS0076`) were excluded specifically from the product-ranking KPI — they're operational line items (postage, fees, etc.), not merchandise, and would distort a "top products" ranking.

## 6. Analysis Methodology

- **Monthly trend:** `resample("ME")` on `Revenue` after setting `InvoiceDate` as the index; month-over-month growth via `.pct_change()`.
- **Top products / countries:** `groupby` + `agg`/`sum`, sorted descending, top 10 taken.
- **Country revenue chart:** top 5 countries shown individually, remainder bucketed into "Other" to keep the donut chart readable.

## 7. Key Findings

- Revenue is strongly **seasonal**, peaking in November both years (£1.47M vs. a ~£650K–£750K mid-year baseline) — consistent with holiday gift-buying.
- **UK concentration risk:** 85% of revenue (£17.87M) comes from a single market; the next-largest (EIRE) is only 3%.
- **AOV of £523.31** across just 5,878 customers points to a wholesale/reseller buyer base rather than typical single-item retail consumers.
- Cancellations (19,494 invoices) and invalid write-offs (2.4% of raw rows) represent a measurable, investigable source of revenue leakage.

## 8. Business Recommendations

1. **Build inventory/marketing lead time for the Q4 peak** — ramp 6–8 weeks ahead of October given the sharp November spike.
2. **Reduce UK dependence** — EIRE, Netherlands, Germany, and France already generate organic revenue without dedicated push; targeted campaigns there are lower-risk growth than further squeezing an already-saturated UK base.
3. **Use proven top sellers as anchor products** — bundle and prioritize placement for the top-10 SKUs (cakestand, t-light holder, bunting, etc.), which have already proven demand at scale.
4. **Investigate cancellations/write-offs** — worth checking whether "damaged"/"check"/"missing" write-offs cluster by product, supplier, or shipping method before treating this as a fixable leakage source (see caveat below).
5. **Segment high-value customers** — identify the top percentile of spenders for a loyalty/wholesale account program, since revenue is concentrated in relatively few high-AOV buyers.

> **Caveat:** Recommendation 4 is the most speculative — the cleaning step removed _invalid_ rows, which isn't proof all of them reflect operational failures rather than messy data entry. Framed as "worth investigating" rather than a confirmed fix.

## 9. Tech Stack & Architecture

- **Analysis:** Python, Pandas (cleaning, KPIs, aggregation).
- **Visualization:** Plotly (line, bar, donut charts) — used both in the notebook and embedded in the Streamlit app.
- **Dashboard app:** `sales_dashboard_final.py` — Streamlit, with:
  - Cached `load_data()` for performance.
  - Sidebar filters: date range, country.
  - KPI cards, monthly revenue line chart, top-10-products bar chart, country revenue donut chart — all wired to the filtered dataset, not the static full dataset.
  - Automated "Business Insights" text block: MoM growth, top market by revenue share (with a guard clause for when only one country is selected), best product by `Description` (not `StockCode`, to avoid duplicate variants fragmenting the ranking), and AOV context — each with guard clauses for empty/insufficient filtered data.

## 10. Known Limitations & Next Steps

- Dataset ends December 2011 — findings reflect that period only, not current market conditions.
- Country-level revenue isn't adjusted for population or market size, so "top market" reflects absolute revenue, not penetration.
- **Next steps:** finalize README with embedded screenshots, deploy the Streamlit app to Streamlit Community Cloud, link the live app in the portfolio site alongside the GitHub repo.
