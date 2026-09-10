"""Export endpoints for streaming CSV and JSON datasets."""

from __future__ import annotations

from typing import Literal
from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

from server.services.export_service import (
    export_analytics_csv,
    export_analytics_summary,
    export_sellers_csv,
    export_sellers_json,
)

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/sellers")
def export_sellers(
    format: Literal["csv", "json"] = Query("csv", description="Export format (csv or json)")
) -> Response:
    """Export complete seller directory dataset in CSV or JSON format."""
    if format == "json":
        data = export_sellers_json()
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": "attachment; filename=sellers_export.json"},
        )

    csv_content = export_sellers_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sellers_export.csv"},
    )


@router.get("/analytics")
def export_analytics(
    format: Literal["csv", "json"] = Query("csv", description="Export format (csv or json)")
) -> Response:
    """Export platform analytics summary in CSV or JSON format."""
    if format == "json":
        data = export_analytics_summary()
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": "attachment; filename=analytics_export.json"},
        )

    csv_content = export_analytics_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
    )
