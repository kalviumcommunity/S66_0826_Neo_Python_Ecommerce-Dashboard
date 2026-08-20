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
uv run python scripts/clean_data.py
uv run python scripts/<analysis_script>.py
uv run jupyter notebook
```

`handle_missing.py` reads the validated CSVs from `data/ingested/`, preserves meaningful Olist nulls, adds missingness indicators, writes outputs to `data/processed/`, and generates treatment reports in `output/missing_data/` plus `output/imputation_decisions.json`.
