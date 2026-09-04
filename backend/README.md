# Seller Trust & Safety Analysis

Combines seller performance, returns, and reviews into a weekly view to identify sustained trust-damaging patterns earlier.

All commands and data paths in this document are relative to `backend/`. This folder contains the existing Python analysis pipelines, not an HTTP API server.

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <project-directory>/backend
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Configure environment variables:

   ```bash
   copy .env.example .env
   ```

## Project Structure

```text
data/raw/        Source data
data/ingested/   Re-exported data after ingestion
data/processed/  Cleaned data
docs/            Data dictionary and analysis documentation
src/             Installable Python package
tests/           Regression tests
scripts/         Python scripts
output/          Generated reports and figures
```

## Running the Analysis

```bash
uv run python scripts/ingest_data.py
uv run python scripts/handle_missing.py
uv run python scripts/deduplicate_data.py
uv run python scripts/transform_datetime.py
uv run python scripts/validate_merges.py
uv run python scripts/analyze_correlations.py
uv run python scripts/investigate_anomalies.py
uv run python scripts/define_kpis.py
uv run python scripts/detect_anomalies.py
uv run python scripts/database_integration.py
uv run python scripts/run_sql_filtering.py
uv run python scripts/validate_sql_joins.py
uv run python scripts/clean_data.py
uv run python scripts/analyze_revenue_distribution.py
uv run python scripts/<analysis_script>.py
uv run jupyter notebook
```

`handle_missing.py` reads the validated CSVs from `data/ingested/`, preserves meaningful Olist nulls, adds missingness indicators, writes outputs to `data/processed/`, and generates treatment reports in `output/missing_data/` plus `output/imputation_decisions.json`.

The `deduplicate_data.py` script analyzes all processed CSVs, removes only confirmed exact duplicate rows from geolocation by default, reports near-duplicate key groups without deleting them, writes the deduplicated geolocation file to `data/processed/deduplicated/`, and creates audit reports under `output/deduplication/`.

The `transform_datetime.py` script parses Olist order event dates with explicit formats, derives purchase day/hour/week/month features, calculates reproducible customer recency, creates weekly and day/hour aggregations, and saves temporal CSVs under `data/processed/temporal/` plus reports and figures under `output/datetime/`. Olist timestamps are timezone-naive in the source, so the workflow does not silently treat them as UTC.

The `validate_merges.py` script validates the processed customer/order integration with an explicit one-to-one left join on `customer_id`, compares inner/left/right/outer row counts, exports unmatched records, and documents key cardinality under `output/merge_validation/`. Payment rows are aggregated by `order_id` before being joined to orders so payment multiplicity cannot create duplicate order rows or double-count revenue. Integrated views are written under `data/processed/integrated/`.

The `analyze_correlations.py` script builds separate order-level and customer-level analytical tables, aggregates one-to-many items/payments/reviews before joining, calculates Pearson and Spearman correlations, flags strong and potentially redundant relationships, and writes matrices, pair reports, and figures under `output/correlation/`. Correlations are documented as associations rather than proof of causation.

The `investigate_anomalies.py` script performs a root-cause investigation on processed Olist data. It isolates unusual order-outcome dates and hours, analyzes payment type, customer state, product category, and order-status patterns, and writes auditable reports and figures under `output/root_cause/`. Because Olist does not include application error logs or payment-provider incidents, the workflow reports evidence and limitations without inventing a causal explanation.

The `analyze_revenue_distribution.py` script analyzes order-level `total_payment_value`, computes descriptive statistics, skewness, excess kurtosis, percentiles, revenue concentration, order/customer segments, and writes plots and tables to `output/revenue_analysis/`.

The `define_kpis.py` script formally defines six business KPIs (Revenue Per Customer, Order Fulfillment Rate, Average Review Score, Late Delivery Rate, Seller Activity Rate, Freight Cost Ratio) — each with a documented formula, data source, target range, owner, and update frequency. It computes each KPI from the processed datasets, validates them against their target ranges, and exports a full JSON report and CSV summary under `output/kpi_report/`.

The `detect_anomalies.py` script performs threshold-based boundary checks and statistical rolling Z-score detection on daily transaction count and revenue series. It flags operational anomalies and logs structured reports (value, expected range, z-score, severity) under `output/anomaly_logs/anomalies_log.json`.

The `database_integration.py` script writes all cleaned, processed Olist CSVs into structured SQLite tables in `data/analytics.db` using SQLAlchemy and Pandas. It validates table column schemas via sqlalchemy.inspect and executes verification aggregation queries, writing the audit details under `output/db_audit/`.

The `run_sql_filtering.py` script executes SQL queries demonstrating pre-aggregation filtering (`WHERE`), dimension grouping (`GROUP BY`), post-aggregation metric thresholds (`HAVING`), and result sorting (`ORDER BY`). It exports targeted operational reports (high-volume underperforming sellers, top revenue product categories, high-volume operating months) to `output/sql_filtering/`.

The `validate_sql_joins.py` script executes relational multi-table JOIN queries, audits row counts and key matches between INNER JOIN and LEFT JOIN, inspects 1:N cardinality expansion, detects orphaned records, and saves reports and samples under `output/sql_joins/`.
