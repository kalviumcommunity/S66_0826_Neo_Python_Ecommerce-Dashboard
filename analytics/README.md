# Offline Analytics Workspace

This workspace contains the Olist CSV data, preparation scripts, validation checks, analytical reports, and analysis-only Python dependencies. It produces the SQLite database used by the FastAPI dashboard API.

## Contents

```text
data/raw/               Original Olist CSV files
data/ingested/          Standardized source copies
data/processed/         Cleaned and derived datasets
scripts/                Ingestion, validation, transformation, and analysis scripts
docs/                   Data dictionary and dashboard-design documentation
output/                 Generated reports, figures, and audit artifacts
tests/                  Offline script and data-workflow tests
```

## Setup

```bash
cd analytics
uv sync --locked
```

The analytics lock file intentionally includes packages such as Matplotlib, Seaborn, Jupyter, and scikit-learn. They remain here rather than in `backend/` so the Vercel API function stays small.

## Typical workflow

Run the scripts in sequence when rebuilding the dashboard data:

```bash
uv run --locked python scripts/ingest_data.py
uv run --locked python scripts/handle_missing.py
uv run --locked python scripts/deduplicate_data.py
uv run --locked python scripts/database_integration.py
uv run --locked python scripts/build_api_cache.py
```

`database_integration.py` writes cleaned datasets to `../backend/server/analytics.db`. `build_api_cache.py` refreshes the precomputed dashboard-risk tables in that same database.

## Validation and analysis

Examples of additional available workflows:

- `validate_merges.py` and `validate_sql_joins.py` audit joins and key integrity.
- `validate_cross_layer_computation.py` compares SQL and Pandas calculations.
- `analyze_correlations.py`, `analyze_revenue_distribution.py`, and `detect_anomalies.py` generate decision-support reports.
- `define_kpis.py` documents and calculates platform KPIs.

Generated artifacts are saved under `output/`.

## Tests

```bash
uv run --locked pytest
```

## Documentation

- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Dashboard thinking and information architecture](docs/DASHBOARD_THINKING.md)

The raw data is historical Olist marketplace data, not a live operational feed. Do not place secrets in this folder or commit local virtual environments.
