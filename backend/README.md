# Backend API

FastAPI service for the Seller Trust & Safety Dashboard. It serves data from the versioned SQLite database at `server/analytics.db` and uses SQL files in `queries/`.

## Contents

```text
api/index.py            Standard Vercel FastAPI entrypoint
server/                 FastAPI routes, services, schemas, and analytics.db
queries/                Parameterized SQL used by API services
tests/                  API and deployment-entrypoint tests
pyproject.toml          API runtime and test dependencies
uv.lock                 Locked backend dependencies
```

## Setup and local run

```bash
cd backend
uv sync --locked
uv run --locked uvicorn server.main:app --reload --port 8000
```

OpenAPI documentation: `http://localhost:8000/docs`; health check: `http://localhost:8000/api/health`.

## API routes

| Group | Routes |
| --- | --- |
| Health | `GET /api/health` |
| Analytics | `GET /api/analytics/overview`, `/review-trend`, `/risk-distribution`, `/review-distribution`, `/category-risk`, `/kpis` |
| Sellers | `GET /api/sellers?page=1&limit=10`, `/api/sellers/filters`, `/api/sellers/{seller_id}` |
| Exports | `GET /api/export/sellers`, `/api/export/analytics` |

## Tests and build

```bash
uv run --locked pytest
uv build
```

## Deployment

Deploy this folder as a Vercel project with Root Directory set to `backend`.

- `api/index.py` is Vercel’s standard FastAPI entrypoint.
- `vercel.json` includes only `api/`, `server/`, and `queries/` in the function bundle.
- Check a deployment using `https://<backend-domain>/api/health`.

The API currently uses permissive CORS for frontend integration. Before a public production release, restrict the allowed origins to the deployed frontend domain.

## Related workspace

Offline data preparation, reports, and analysis dependencies live in [`../analytics/`](../analytics/README.md). They are deliberately not included in this deployable backend.
