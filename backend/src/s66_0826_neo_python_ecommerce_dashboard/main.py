"""FastAPI application initialization and server entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from s66_0826_neo_python_ecommerce_dashboard.routers import analytics, export, sellers

app = FastAPI(
    title="Seller Trust & Safety Dashboard API",
    description=(
        "Production backend API powering the Seller Risk & Trust Dashboard with "
        "real dataset-derived metrics, multi-level information pyramid support, "
        "and PRD KPI validations."
    ),
    version="0.1.0",
)


# CORS middleware for seamless frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount application routers
app.include_router(analytics.router)
app.include_router(sellers.router)
app.include_router(export.router)


@app.get("/api/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "service": "seller-trust-safety-api"}


def main() -> None:
    """Run the Uvicorn server directly."""
    import uvicorn

    uvicorn.run(
        "s66_0826_neo_python_ecommerce_dashboard.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
