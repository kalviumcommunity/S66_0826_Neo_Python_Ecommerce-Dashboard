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

# run the workflow (data/raw -> output)
uv run python scripts/clean_data.py

# capture stdout for submission
uv run python scripts/clean_data.py > output/sample_run.txt 2>&1
```

What it does
- Ingest: read all CSVs in `data/raw/`.
- Process: normalize columns, drop duplicates, fill numeric nulls with medians, parse date-like columns.
- Output: write cleaned CSVs to `output/` and log to `output/data_cleaning.log`.

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
- No output files: confirm `data/raw/` contains CSVs and re-run.

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
