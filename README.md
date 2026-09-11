# Seller Trust & Safety Dashboard

A full-stack data product that helps marketplace teams identify seller trust and operational-risk signals in the Olist Brazilian e-commerce dataset.

## What the product delivers

- Seller risk scores based on delayed deliveries, low review ratings, and order cancellations.
- Executive metrics, trends, risk tiers, and high-risk product-category comparisons.
- A paginated seller directory, seller investigation view, and CSV/JSON exports.
- A reproducible offline analytics workflow that prepares the data used by the API.

## Project map

| Folder | Purpose | Read more |
| --- | --- | --- |
| [`frontend/`](frontend/) | Next.js dashboard users interact with. | [Frontend README](frontend/README.md) |
| [`backend/`](backend/) | Deployable FastAPI service, API SQL, and SQLite dashboard database. | [Backend README](backend/README.md) |
| [`analytics/`](analytics/) | Offline CSV data, preparation scripts, validation, and reports. | [Analytics README](analytics/README.md) |
| [`.github/workflows/`](.github/workflows/) | Pull-request CI and production deployment workflows. | [CI/CD workflows](.github/workflows/) |

## Architecture

```text
Olist CSV data → analytics/ scripts → backend/server/analytics.db
                                         ↓
                                FastAPI backend API
                                         ↓
                              Next.js frontend dashboard
```

The analytics workspace is separate from the deployable backend so large CSVs,
notebooks, reports, and analysis packages are never bundled into the Vercel API function.

## Data source

The project uses the historical [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): customers, sellers, orders, items, payments, reviews, products, and geolocation reference data. Values are in Brazilian reais (BRL). See the [data dictionary](analytics/docs/DATA_DICTIONARY.md).

## Quick start

Prerequisites: Node.js 24, npm, Python 3.14, and [uv](https://docs.astral.sh/uv/).

```bash
# Terminal 1: API
cd backend
uv sync --locked
uv run --locked uvicorn server.main:app --reload --port 8000

# Terminal 2: dashboard
cd ../frontend
cp .env.example .env.local
npm ci
npm run dev
```

Set this value in `frontend/.env.local` before starting the dashboard:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open `http://localhost:3000`. The API health route is `http://localhost:8000/api/health`.

## Quality checks

```bash
cd backend && uv run --locked pytest && uv build
cd ../analytics && uv run --locked pytest
cd ../frontend && npm run lint && npm run build
```

GitHub Actions runs backend, analytics, and frontend checks on pull requests. Production deployments run after successful checks on `main`.

## Submission materials

- [Dashboard information architecture](analytics/docs/DASHBOARD_THINKING.md)
- [Data dictionary](analytics/docs/DATA_DICTIONARY.md)
- Add links to the team’s existing PRD and UX mock-up here before final submission so reviewers can reach every required artifact from this README.

## Security and data notes

Never commit `.env`, `.env.local`, Vercel tokens, or other credentials. The deployed backend reads its bundled SQLite database from read-only serverless storage; browser-only investigation flags do not persist after refresh.
