"""Integration tests for Seller Trust & Safety API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_analytics_overview() -> None:
    """Verify Level 1 Overview metrics endpoint returns real calculated data."""
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()

    assert "total_sellers" in data
    assert data["total_sellers"] > 0
    assert "high_risk_sellers" in data
    assert data["high_risk_sellers"] >= 0
    assert "high_risk_change_percent" in data
    assert "average_review_score" in data
    assert 1.0 <= data["average_review_score"] <= 5.0
    assert "late_delivery_percentage" in data
    assert 0.0 <= data["late_delivery_percentage"] <= 100.0
    assert "cancellation_rate" in data
    assert 0.0 <= data["cancellation_rate"] <= 100.0

    assert "targets" in data
    assert data["targets"]["average_review_score"] == 4.0
    assert "badges" in data
    assert "review_score_status" in data["badges"]


def test_analytics_review_trend() -> None:
    """Verify Level 2 Review trend endpoint returns monthly historical trend with target."""
    response = client.get("/api/analytics/review-trend")
    assert response.status_code == 200
    data = response.json()

    assert data["target_score"] == 4.0
    assert "trend" in data
    assert len(data["trend"]) > 0

    first_point = data["trend"][0]
    assert "period" in first_point
    assert "average_review_score" in first_point
    assert 1.0 <= first_point["average_review_score"] <= 5.0


def test_analytics_risk_distribution() -> None:
    """Verify Level 3 Risk distribution endpoint returns seller counts per tier."""
    response = client.get("/api/analytics/risk-distribution")
    assert response.status_code == 200
    data = response.json()

    assert "low" in data
    assert "medium" in data
    assert "high" in data
    assert "total" in data
    assert data["total"] == data["low"] + data["medium"] + data["high"]
    assert data["total"] > 0


def test_analytics_review_distribution() -> None:
    """Verify Level 3 Review star rating distribution and positive percentage."""
    response = client.get("/api/analytics/review-distribution")
    assert response.status_code == 200
    data = response.json()

    dist = data["distribution"]
    assert "1_star" in dist
    assert "2_star" in dist
    assert "3_star" in dist
    assert "4_star" in dist
    assert "5_star" in dist

    total_stars = sum(dist.values())
    assert total_stars > 0
    assert "positive_review_percentage" in data
    assert 0.0 <= data["positive_review_percentage"] <= 100.0


def test_analytics_category_risk() -> None:
    """Verify Level 3 Category risk endpoint returns ranked product categories."""
    response = client.get("/api/analytics/category-risk")
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert len(data["categories"]) > 0

    first_cat = data["categories"][0]
    assert "category" in first_cat
    assert "risk_score" in first_cat
    assert 0.0 <= first_cat["risk_score"] <= 100.0


def test_analytics_formal_kpis() -> None:
    """Verify PRD formal platform KPIs endpoint returns 6 validated business KPIs."""
    response = client.get("/api/analytics/kpis")
    assert response.status_code == 200
    data = response.json()

    assert data["total_kpis"] >= 6
    assert len(data["kpis"]) >= 6
    kpi_names = [k["kpi_name"] for k in data["kpis"]]
    assert "Revenue Per Customer" in kpi_names
    assert "Order Fulfillment Rate" in kpi_names
    assert "Average Review Score" in kpi_names
    assert "Late Delivery Rate" in kpi_names
    assert "Seller Activity Rate" in kpi_names
    assert "Freight Cost Ratio" in kpi_names


def test_sellers_directory_and_filters() -> None:
    """Verify Level 4 Seller directory listing, pagination, and filter options."""
    # 1. Filter options
    filter_res = client.get("/api/sellers/filters")
    assert filter_res.status_code == 200
    filters = filter_res.json()
    assert len(filters["categories"]) > 0
    assert "LOW" in filters["risk_tiers"]
    assert "Delivery Delays" in filters["risk_drivers"]

    # 2. Directory listing (default page)
    res = client.get("/api/sellers?page=1&limit=10")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] > 0
    assert body["page"] == 1
    assert body["limit"] == 10
    assert len(body["sellers"]) == 10

    seller = body["sellers"][0]
    assert "seller_id" in seller
    assert "category" in seller
    assert "location" in seller
    assert "city" in seller["location"]
    assert "state" in seller["location"]
    assert "risk_score" in seller
    assert "risk_tier" in seller
    assert "primary_risk_driver" in seller
    assert "total_orders" in seller
    assert "is_sparse" in seller
    assert "average_rating" in seller
    assert "late_delivery_percentage" in seller
    assert "risk_history" in seller

    # 3. Filtering by risk tier
    high_res = client.get("/api/sellers?risk_tier=HIGH")
    assert high_res.status_code == 200
    high_body = high_res.json()
    for s in high_body["sellers"]:
        assert s["risk_tier"] == "HIGH"

    # 4. Search filter
    search_res = client.get(f"/api/sellers?search={seller['seller_id'][:8]}")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1


def test_seller_details() -> None:
    """Verify Level 4 Detailed seller profile endpoint."""
    # Pick a valid seller from directory
    list_res = client.get("/api/sellers?limit=1")
    seller_id = list_res.json()["sellers"][0]["seller_id"]

    res = client.get(f"/api/sellers/{seller_id}")
    assert res.status_code == 200
    detail = res.json()

    assert detail["seller_id"] == seller_id
    assert "metrics" in detail
    assert "total_orders" in detail["metrics"]
    assert "total_revenue" in detail["metrics"]
    assert "avg_delivery_days" in detail["metrics"]
    assert "risk_contributors" in detail
    assert "monthly_history" in detail

    # 404 for non-existent seller
    not_found = client.get("/api/sellers/non_existent_seller_123456789")
    assert not_found.status_code == 404


def test_export_endpoints() -> None:
    """Verify CSV and JSON export endpoints for sellers and analytics."""
    # 1. Sellers CSV export
    s_csv = client.get("/api/export/sellers?format=csv")
    assert s_csv.status_code == 200
    assert "text/csv" in s_csv.headers["content-type"]
    assert "seller_id,category" in s_csv.text

    # 2. Sellers JSON export
    s_json = client.get("/api/export/sellers?format=json")
    assert s_json.status_code == 200
    assert isinstance(s_json.json(), list)

    # 3. Analytics CSV export
    a_csv = client.get("/api/export/analytics?format=csv")
    assert a_csv.status_code == 200
    assert "text/csv" in a_csv.headers["content-type"]
    assert "section,metric_name" in a_csv.text

    # 4. Analytics JSON export
    a_json = client.get("/api/export/analytics?format=json")
    assert a_json.status_code == 200
    assert "overview" in a_json.json()


def test_sqlalchemy_orm_models_and_queries() -> None:
    """Verify SQLAlchemy ORM models query correctly and queries are loaded from .sql files."""
    from server.database import SessionLocal
    from server.models import Order, OrderItem, OrderReview, Seller
    from server.queries import load_query

    # Verify query loader
    query_text = load_query("analytics_macro_overview.sql")
    assert "SELECT" in query_text
    assert "orders" in query_text

    # Verify ORM queries
    with SessionLocal() as session:
        order_count = session.query(Order).count()
        assert order_count > 0

        seller_count = session.query(Seller).count()
        assert seller_count > 0

        review_sample = session.query(OrderReview).first()
        assert review_sample is not None
        assert hasattr(review_sample, "review_score")
