# Offline Analytics Workspace

This folder contains the Olist CSV datasets, offline data-preparation scripts,
reports, and their analysis dependencies. It is intentionally separate from the
deployable FastAPI backend.

```bash
cd analytics
uv sync
uv run python scripts/ingest_data.py
```

Scripts that update the dashboard database write to
`../backend/server/analytics.db`.
