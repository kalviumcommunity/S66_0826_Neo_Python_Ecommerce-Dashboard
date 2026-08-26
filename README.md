# Seller Trust & Safety Analysis

Combines seller performance, returns, and reviews into a weekly view to identify sustained trust-damaging patterns earlier.

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <project-directory>
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
notebooks/       Jupyter analysis
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
uv run python scripts/feature_engineering.py
uv run python scripts/time_series_analysis.py
uv run python scripts/clean_data.py
uv run python scripts/<analysis_script>.py
uv run jupyter notebook
```

`handle_missing.py` reads the validated CSVs from `data/ingested/`, preserves meaningful Olist nulls, adds missingness indicators, writes outputs to `data/processed/`, and generates treatment reports in `output/missing_data/` plus `output/imputation_decisions.json`.

The `deduplicate_data.py` script analyzes all processed CSVs, removes only confirmed exact duplicate rows from geolocation by default, reports near-duplicate key groups without deleting them, writes the deduplicated geolocation file to `data/processed/deduplicated/`, and creates audit reports under `output/deduplication/`.

The `transform_datetime.py` script parses Olist order event dates with explicit formats, derives purchase day/hour/week/month features, calculates reproducible customer recency, creates weekly and day/hour aggregations, and saves temporal CSVs under `data/processed/temporal/` plus reports and figures under `output/datetime/`. Olist timestamps are timezone-naive in the source, so the workflow does not silently treat them as UTC.

The `feature_engineering.py` script computes value-driving ratios (spend per order, freight ratio, late delivery ratio), tiered/binned features using `pd.cut` and `pd.qcut` (customer spend tiers, seller activity tiers, freight tiers), and composite business scores (Customer RFM score & segment, Seller Trust/Risk score). Feature datasets are written under `data/processed/features/` and summary reports are saved under `output/feature_engineering/`.

The `time_series_analysis.py` script builds daily, weekly, and monthly order and revenue time-series from the processed temporal data. It applies 7-day and 30-day rolling averages to smooth noise, computes week-over-week and month-over-month percentage changes using `.pct_change()`, calculates cumulative orders and revenue via `.cumsum()`, and derives executive trend insights (acceleration/deceleration, growth streaks). Time-series datasets are written under `data/processed/time_series/` and reports are saved under `output/time_series_analysis/`. Olist timestamps are timezone-naive in the source, so the workflow does not silently treat them as UTC.

The `validate_merges.py` script validates the processed customer/order integration with an explicit one-to-one left join on `customer_id`, compares inner/left/right/outer row counts, exports unmatched records, and documents key cardinality under `output/merge_validation/`. Payment rows are aggregated by `order_id` before being joined to orders so payment multiplicity cannot create duplicate order rows or double-count revenue. Integrated views are written under `data/processed/integrated/`.
