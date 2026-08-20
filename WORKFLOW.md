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
