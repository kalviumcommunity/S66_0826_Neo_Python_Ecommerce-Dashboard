# Frontend Dashboard

Next.js dashboard for exploring seller trust and risk data supplied by the FastAPI backend.

## Features

- Marketplace overview and seller-risk summary.
- Review, delivery, cancellation, and category-risk charts.
- Searchable and paginated seller directory.
- Seller detail view with risk-factor breakdown, reviews, and order evidence.
- CSV and JSON data exports.

## Requirements

- Node.js 24
- npm
- A running FastAPI backend URL

## Environment configuration

Copy the example file:

```bash
cp .env.example .env.local
```

Set the API base URL without a trailing slash:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_API_URL` is intentionally available to the browser; it must contain only the public backend URL, never a secret.

## Run locally

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`.

## Quality checks

```bash
npm run lint
npx tsc --noEmit
npm run build
```

If `next` is not recognized, dependencies have not been installed. Run `npm ci` again from this folder.

## API integration

The dashboard requests these API groups from `NEXT_PUBLIC_API_URL`:

- `/api/analytics/*` for overview, trends, distributions, categories, and KPIs.
- `/api/sellers` for the directory, filters, and seller details.
- `/api/export/*` for exports.

The API health check is `<backend-url>/api/health`.

## Deployment

Deploy this folder as a separate Vercel project with Root Directory set to `frontend`.

Add `NEXT_PUBLIC_API_URL` as a **Config** environment variable in Vercel for Production, and Preview if branch deployments should call the API. Redeploy after changing this value because Next.js embeds public environment variables during the build.
