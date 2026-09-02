WORKFLOW: Data Cleaning Script

Purpose
- How to run `scripts/clean_data.py`, capture sample output, and debug common issues.

Prerequisites
- `uv` in PATH and project dependencies installed (see `pyproject.toml`).
- Run from the repository root.
- Recommended: use the pinned Python runtime (3.14).

Quick commands

```bash
# (optional) pin Python to a compatible runtime
uv python pin 3.14

# (optional) sync the virtualenv
uv sync

# ingest source CSVs (data/raw -> data/ingested)
uv run python scripts/ingest_data.py

# analyze and handle missing values (data/ingested -> data/processed)
uv run python scripts/handle_missing.py

# detect duplicates and remove confirmed geolocation exact duplicates
uv run python scripts/deduplicate_data.py

# transform dates and create temporal features, metrics, reports, and figures
uv run python scripts/transform_datetime.py

# validate customer/order/payment joins and create integrated views
uv run python scripts/validate_merges.py

# analyze Pearson/Spearman relationships on aggregated order/customer metrics
uv run python scripts/analyze_correlations.py
# investigate time-window anomalies and document evidence-based hypotheses
uv run python scripts/investigate_anomalies.py
# compute and validate key performance indicators
uv run python scripts/define_kpis.py
# execute fixed-threshold and rolling z-score anomaly detection
uv run python scripts/detect_anomalies.py
# load processed files into SQLite database and audit schema
uv run python scripts/database_integration.py

# run the legacy/general cleaning workflow if needed
uv run python scripts/clean_data.py

# capture stdout for submission
uv run python scripts/clean_data.py > output/sample_run.txt 2>&1
```

What the missing-data workflow does
- Reads the ingested CSVs from `data/ingested/`.
- Profiles missing values before treatment.
- Preserves meaningful review-text, order-event, and product-catalog nulls.
- Adds missingness indicators and a derived `unknown` product-category field for analysis.
- Writes processed CSVs to `data/processed/`.
- Writes per-dataset reports and summaries to `output/missing_data/`.
- Writes the auditable decision log to `output/imputation_decisions.json`.

The existing `clean_data.py` remains available as a separate general cleaning workflow.

The deduplication workflow reads `data/processed/`, writes the confirmed geolocation result to `data/processed/deduplicated/`, reports near-duplicate candidates without removing them, and saves audit files under `output/deduplication/`.

The date and time workflow reads the processed orders and payments tables, parses Olist date columns with explicit formats, derives vectorized calendar features, calculates customer recency, aggregates weekly and day/hour activity, and writes derived files to `data/processed/temporal/`. Reports and figures are saved under `output/datetime/`. Because Olist source timestamps do not include timezone offsets, they remain timezone-naive and are not assumed to be UTC.

The merge-validation workflow reads from `data/processed/`, validates the one-to-one customer/order left join on `customer_id`, compares all four join types, exports unmatched records, and writes decisions under `output/merge_validation/`. It aggregates the many-side payment table by `order_id` before joining to the order-level data. Integrated outputs are written to `data/processed/integrated/`; source datasets are not modified.

The correlation workflow reads processed Olist tables, aggregates item/payment/review records to order level before joining, creates separate order- and customer-level features, calculates Pearson and Spearman matrices, and writes relationship reports and figures under `output/correlation/`. Strong correlations are flagged for interpretation or feature review, but no causal conclusions or automatic feature removal are made.
The root-cause workflow reads processed Olist orders, payments, customers, items, and products. It parses `order_purchase_timestamp` explicitly, uses delivered status as an operational fulfillment-success proxy, isolates low-success dates and hours, analyzes payment/state/category segments, creates crosstabs and figures, and writes an evidence-limited investigation report under `output/root_cause/`. Olist has no application error logs or payment-provider incident data, so the workflow does not invent an external cause and marks external validation as unavailable unless supplied separately.
The KPI validation workflow reads from `data/processed/`, computes six platform-wide metrics (Revenue Per Customer, Order Fulfillment Rate, Average Review Score, Late Delivery Rate, Seller Activity Rate, Freight Cost Ratio), compares each against its target range, and exports full JSON validation logs, a flat CSV summary, and a KPI catalogue template under `output/kpi_report/`.

The anomaly detection workflow aggregates e-commerce data to contiguous daily intervals, performs absolute boundary checks (daily orders, low and high revenue limits), calculates rolling 14-day Z-scores to spot statistical fluctuations, and saves a structured JSON audit log and CSV summaries under `output/anomaly_logs/`.

The database integration workflow establishes connection to a local SQLite database (`data/analytics.db`), loads core cleaned datasets to SQL tables using Pandas `to_sql()`, runs database column schema inspections, and executes verification aggregation queries. The validation summary is exported under `output/db_audit/`.

Sample output (excerpt)

```
Starting data cleaning workflow...
Processing olist_customers_dataset.csv...
✓ Saved 99441 records to /path/to/project/output/olist_customers_dataset.csv
...
Workflow completed successfully.
```

Troubleshooting
- Missing pandas: run `uv sync`, then test imports:

```bash
uv run python -c "import pandas; import numpy; print(pandas.__version__, numpy.__version__)"
```

- Segfaults/import crashes: pin to 3.13 and `uv sync`.
- No output files: confirm `data/ingested/` contains CSVs and run `scripts/ingest_data.py` first.

Save sample output
- Capture and optionally commit:

```bash
uv run python scripts/clean_data.py > output/sample_run.txt 2>&1
git add output/sample_run.txt
git commit -m "chore: add data cleaning sample run output"
```

Notes
- The script is import-safe (`if __name__ == "__main__"`) and creates `output/` if missing.
- I can run it and add `output/sample_run.txt` to the repo if you want.
