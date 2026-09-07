# Seller Trust & Safety Dashboard

This repository contains independently managed Python analysis and Next.js frontend projects.

## Structure

```text
backend/
  data/              Raw, ingested, and processed datasets
  docs/              Data dictionary
  output/            Existing analysis reports and figures
  scripts/           Python analysis and validation pipelines
  src/               Installable Python package
  tests/             Python tests
  pyproject.toml     Python dependencies and project configuration
  uv.lock            Locked Python dependencies
frontend/            Next.js dashboard and its npm dependencies
.github/workflows/   Python CI and frontend CI/deployment
```

## Backend

Requires uv and Python 3.14:

```bash
cd backend
uv sync --locked
uv run pytest
uv run python scripts/ingest_data.py
uv run python scripts/run_sql_filtering.py
uv run python scripts/validate_sql_joins.py
uv run python scripts/build_sql_views_and_aggregations.py
```

See [backend setup and analysis commands](backend/README.md), [workflow guide](backend/WORKFLOW.md), and [data dictionary](backend/docs/DATA_DICTIONARY.md).
From the repository root, use `uv run --directory backend pytest` or `uv run --directory backend python scripts/<script>.py`.

The Python project currently provides batch analysis pipelines, not a web API. Its data and output paths resolve inside `backend/`.

## Frontend

Requires Node.js 24:

```bash
cd frontend
npm ci
npm run dev
```

See [frontend documentation](frontend/README.md). The dashboard currently uses mock data and is not connected to the Python pipelines.

## Checks

```bash
cd backend
uv run pytest
cd ../frontend
npm run lint
npm run build
```

GitHub Actions runs each project's commands from its own directory. The existing Vercel deployment step remains at repository root; configure the Vercel project's Root Directory as `frontend` and provide its deployment credentials in GitHub settings.

## Local files after restructuring

### Teammates pulling the folder migration

Commit or stash any local work before pulling. Once the migration is committed and merged, pull the updated branch, then open a new terminal at the repository root (or run `deactivate` if an old Python virtual environment is active).

Install Node.js 24 and uv if they are not already available. Run these commands on Windows, macOS, or Linux:

```bash
cd backend
uv sync --locked
uv run --locked pytest
cd ../frontend
npm ci
npm run lint
npm run build
npm run dev
```

uv uses `backend/.python-version` to select Python 3.14 and can download it if needed. The lockfiles must be committed with the migration; do not regenerate them just to set up a teammate's machine. `npm ci` recreates `frontend/node_modules` from its lockfile. Internet access is needed for uncached dependencies, Python downloads, and the frontend's build-time Google Fonts downloads.

No API keys or Vercel credentials are required to run the current mock-data dashboard or the existing Python tests. Existing private environment files are not moved by Git. If you have custom backend environment variables or untracked datasets, copy them to the corresponding location inside `backend/` yourself without overwriting the tracked datasets. Next.js-specific local variables belong in `frontend/.env.local`; a repository-root `.env.local` is not automatically loaded by the frontend.

Update IDE Python interpreter settings to `backend/.venv/Scripts/python.exe` on Windows or `backend/.venv/bin/python` on macOS/Linux. Update custom run configurations to use `backend` as their working directory. Old root-level commands such as `uv run python scripts/ingest_data.py` must now run inside `backend/`, or use `uv run --directory backend python scripts/ingest_data.py` from the root.

Python CI installs from the lockfile and runs tests on Windows, macOS, and Linux. Frontend CI performs a clean install, lint, and production build on Linux. These remote checks must pass on the pull request before merging; local checks alone do not guarantee every teammate's machine configuration.

An existing root `.venv/` is left untouched because virtual environments are not portable. Run `uv sync --locked` inside `backend/` to create `backend/.venv/`. Do not move the old environment manually.

Root `.env.local` and `.vercel/` settings remain untouched. Put backend-specific variables in `backend/.env` when needed; never commit secrets. The root `.gitignore` covers both projects.
