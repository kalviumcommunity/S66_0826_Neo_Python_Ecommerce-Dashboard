# Neo — Seller Risk & Trust Dashboard

Next.js port of the supplied Olist seller risk dashboard. The original components, charts, styling, and sample seller records live in `features/seller-risk`; `app/page.tsx` renders the dashboard.

Includes operational overview charts, searchable/filterable seller directory, seller detail tabs, review filters, investigation flagging, and CSV/JSON exports.

This is a mock-data frontend. Flags exist only in memory and reset on refresh. Flagging does not hold payouts, notify a team, or create a backend investigation, despite the reference UI's demonstration copy. Marketplace summary metrics describe the reference dataset; the directory contains 10 example sellers.

Run commands below from `frontend`. Validate changes with `npm run lint`, `npx tsc --noEmit`, and `npm run build`.

## Getting Started

Use Node.js 24 and npm 11.18.0 (the version pinned in CI). To install with that npm version without changing your global npm installation:

```bash
npx --yes --package=npm@11.18.0 npm ci
```

When dependency changes require a lockfile update, use `npx --yes --package=npm@11.18.0 npm install --package-lock-only`, then verify with the clean-install command above. Older npm versions can accept incomplete optional dependency entries that newer CI rejects. Commit `package-lock.json` alongside dependency changes.

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses `next/font` to self-host Inter and JetBrains Mono, matching the reference typography. The first build requires access to Google Fonts to download them.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
