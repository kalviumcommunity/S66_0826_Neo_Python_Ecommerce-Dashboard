"""KPI Definition and Computation Pipeline for Seller Trust & Safety Analysis.

Formally defines, computes, and validates six business KPIs for the Olist
e-commerce platform. Each KPI has a documented name, formula, data source,
target range, owner, and update frequency. Computed values are validated
against their target ranges and exported as structured reports.

KPIs defined:
  1. Revenue Per Customer
  2. Order Fulfillment Rate
  3. Average Review Score
  4. Late Delivery Rate
  5. Seller Activity Rate (active sellers / total sellers)
  6. Freight Cost Ratio (freight as % of item price)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output" / "kpi_report"


# ---------------------------------------------------------------------------
# KPI Definition Schema
# ---------------------------------------------------------------------------

@dataclass
class KPIDefinition:
    """Formal KPI specification — name, formula, source, target, and metadata."""

    name: str
    description: str
    formula: str
    data_source: list[str]
    target_min: float | None
    target_max: float | None
    unit: str
    owner: str
    update_frequency: str


# ---------------------------------------------------------------------------
# Catalogue of KPIs for the Olist platform
# ---------------------------------------------------------------------------

KPI_CATALOGUE: list[KPIDefinition] = [
    KPIDefinition(
        name="Revenue Per Customer",
        description=(
            "Average total payment value earned per unique customer. "
            "Measures how much each customer contributes to platform revenue."
        ),
        formula="SUM(payment_value) / COUNT(DISTINCT customer_unique_id)",
        data_source=["olist_order_payments_dataset.csv", "olist_customers_dataset.csv", "olist_orders_dataset.csv"],
        target_min=100.0,
        target_max=300.0,
        unit="BRL",
        owner="Revenue Analytics",
        update_frequency="Monthly",
    ),
    KPIDefinition(
        name="Order Fulfillment Rate",
        description=(
            "Proportion of orders that were successfully delivered to the customer. "
            "Indicates logistics reliability and operational quality."
        ),
        formula="COUNT(order_id WHERE order_status = 'delivered') / COUNT(order_id) * 100",
        data_source=["olist_orders_dataset.csv"],
        target_min=90.0,
        target_max=100.0,
        unit="%",
        owner="Operations",
        update_frequency="Weekly",
    ),
    KPIDefinition(
        name="Average Review Score",
        description=(
            "Mean customer satisfaction score across all reviewed orders. "
            "Scores range from 1 (worst) to 5 (best)."
        ),
        formula="AVG(review_score) WHERE review_score IS NOT NULL",
        data_source=["olist_order_reviews_dataset.csv"],
        target_min=3.8,
        target_max=5.0,
        unit="score (1-5)",
        owner="Customer Experience",
        update_frequency="Weekly",
    ),
    KPIDefinition(
        name="Late Delivery Rate",
        description=(
            "Proportion of delivered orders where the actual delivery date exceeded "
            "the estimated delivery date. Lower is better."
        ),
        formula=(
            "COUNT(order_id WHERE order_delivered_customer_date > order_estimated_delivery_date) "
            "/ COUNT(order_id WHERE order_status = 'delivered') * 100"
        ),
        data_source=["olist_orders_dataset.csv"],
        target_min=0.0,
        target_max=10.0,
        unit="%",
        owner="Logistics",
        update_frequency="Weekly",
    ),
    KPIDefinition(
        name="Seller Activity Rate",
        description=(
            "Proportion of registered sellers that have fulfilled at least one order. "
            "Indicates how many sellers on the platform are actively contributing."
        ),
        formula=(
            "COUNT(DISTINCT seller_id WHERE order_count >= 1) "
            "/ COUNT(DISTINCT seller_id) * 100"
        ),
        data_source=["olist_sellers_dataset.csv", "olist_order_items_dataset.csv"],
        target_min=70.0,
        target_max=100.0,
        unit="%",
        owner="Seller Growth",
        update_frequency="Monthly",
    ),
    KPIDefinition(
        name="Freight Cost Ratio",
        description=(
            "Freight value as a percentage of total order item price. "
            "High ratios indicate shipping is expensive relative to product value."
        ),
        formula="SUM(freight_value) / (SUM(price) + SUM(freight_value)) * 100",
        data_source=["olist_order_items_dataset.csv"],
        target_min=0.0,
        target_max=25.0,
        unit="%",
        owner="Pricing & Logistics",
        update_frequency="Monthly",
    ),
]


# ---------------------------------------------------------------------------
# Data Loaders
# ---------------------------------------------------------------------------

def _read(filename: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required processed file not found: {path}")
    return pd.read_csv(path, dtype=DATASET_DTYPES.get(filename))


# ---------------------------------------------------------------------------
# KPI Computation Functions
# ---------------------------------------------------------------------------

def compute_revenue_per_customer(
    orders: pd.DataFrame,
    payments: pd.DataFrame,
    customers: pd.DataFrame,
) -> float:
    """Revenue Per Customer = total payment value / distinct customer count."""
    total_revenue = payments["payment_value"].sum()
    # Join orders → customers to get unique customer_unique_id per order
    order_customer = orders[["order_id", "customer_id"]].merge(
        customers[["customer_id", "customer_unique_id"]], on="customer_id", how="left"
    )
    unique_customers = order_customer["customer_unique_id"].nunique()
    return round(total_revenue / unique_customers, 2) if unique_customers else 0.0


def compute_order_fulfillment_rate(orders: pd.DataFrame) -> float:
    """Order Fulfillment Rate = delivered orders / total orders * 100."""
    total = len(orders)
    delivered = (orders["order_status"] == "delivered").sum()
    return round(delivered / total * 100, 2) if total else 0.0


def compute_avg_review_score(reviews: pd.DataFrame) -> float:
    """Average Review Score = mean of review_score (non-null)."""
    valid = reviews["review_score"].dropna()
    return round(float(valid.mean()), 4) if len(valid) else 0.0


def compute_late_delivery_rate(orders: pd.DataFrame) -> float:
    """Late Delivery Rate = late delivered orders / total delivered orders * 100."""
    delivered = orders[orders["order_status"] == "delivered"].copy()
    delivered["order_delivered_customer_date"] = pd.to_datetime(
        delivered["order_delivered_customer_date"], errors="coerce"
    )
    delivered["order_estimated_delivery_date"] = pd.to_datetime(
        delivered["order_estimated_delivery_date"], errors="coerce"
    )
    valid = delivered.dropna(
        subset=["order_delivered_customer_date", "order_estimated_delivery_date"]
    )
    if len(valid) == 0:
        return 0.0
    late = (
        valid["order_delivered_customer_date"] > valid["order_estimated_delivery_date"]
    ).sum()
    return round(late / len(valid) * 100, 2)


def compute_seller_activity_rate(
    sellers: pd.DataFrame, order_items: pd.DataFrame
) -> float:
    """Seller Activity Rate = active sellers (>=1 order) / total sellers * 100."""
    total_sellers = sellers["seller_id"].nunique()
    active_sellers = order_items["seller_id"].nunique()
    return round(active_sellers / total_sellers * 100, 2) if total_sellers else 0.0


def compute_freight_cost_ratio(order_items: pd.DataFrame) -> float:
    """Freight Cost Ratio = total freight / (total price + total freight) * 100."""
    total_price = order_items["price"].sum()
    total_freight = order_items["freight_value"].sum()
    denominator = total_price + total_freight
    return round(total_freight / denominator * 100, 2) if denominator else 0.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_kpi(
    kpi_def: KPIDefinition, computed_value: float
) -> dict[str, Any]:
    """Compare a computed KPI value against its defined target range."""
    within_target = True
    status = "PASS"
    deviation_notes: list[str] = []

    if kpi_def.target_min is not None and computed_value < kpi_def.target_min:
        within_target = False
        status = "FAIL"
        deviation_notes.append(
            f"Value {computed_value}{kpi_def.unit} is below minimum target "
            f"{kpi_def.target_min}{kpi_def.unit}."
        )
    if kpi_def.target_max is not None and computed_value > kpi_def.target_max:
        within_target = False
        status = "FAIL"
        deviation_notes.append(
            f"Value {computed_value}{kpi_def.unit} exceeds maximum target "
            f"{kpi_def.target_max}{kpi_def.unit}."
        )

    return {
        "kpi_name": kpi_def.name,
        "description": kpi_def.description,
        "formula": kpi_def.formula,
        "data_source": kpi_def.data_source,
        "owner": kpi_def.owner,
        "update_frequency": kpi_def.update_frequency,
        "unit": kpi_def.unit,
        "target_min": kpi_def.target_min,
        "target_max": kpi_def.target_max,
        "computed_value": computed_value,
        "within_target": within_target,
        "status": status,
        "deviation_notes": deviation_notes,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute and validate platform KPIs for the Olist dataset."
    )
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting KPI computation pipeline...")

    # Load datasets
    orders = _read("olist_orders_dataset.csv")
    payments = _read("olist_order_payments_dataset.csv")
    customers = _read("olist_customers_dataset.csv")
    reviews = _read("olist_order_reviews_dataset.csv")
    sellers = _read("olist_sellers_dataset.csv")
    order_items = _read("olist_order_items_dataset.csv")

    # Map KPI name → (definition, computed value)
    computations: dict[str, float] = {
        "Revenue Per Customer": compute_revenue_per_customer(orders, payments, customers),
        "Order Fulfillment Rate": compute_order_fulfillment_rate(orders),
        "Average Review Score": compute_avg_review_score(reviews),
        "Late Delivery Rate": compute_late_delivery_rate(orders),
        "Seller Activity Rate": compute_seller_activity_rate(sellers, order_items),
        "Freight Cost Ratio": compute_freight_cost_ratio(order_items),
    }

    # Validate each KPI against its definition
    results: list[dict[str, Any]] = []
    kpi_map = {kpi.name: kpi for kpi in KPI_CATALOGUE}

    for kpi_name, computed_value in computations.items():
        kpi_def = kpi_map[kpi_name]
        result = validate_kpi(kpi_def, computed_value)
        results.append(result)
        status_icon = "✓" if result["status"] == "PASS" else "✗"
        print(
            f"  {status_icon} [{result['status']}] {kpi_name}: "
            f"{computed_value} {kpi_def.unit} "
            f"(target: {kpi_def.target_min}–{kpi_def.target_max} {kpi_def.unit})"
        )

    # Export full JSON report
    kpi_report = {
        "pipeline": "KPI Definition & Validation",
        "dataset": "Olist Brazilian E-Commerce",
        "total_kpis": len(results),
        "passing": sum(1 for r in results if r["status"] == "PASS"),
        "failing": sum(1 for r in results if r["status"] == "FAIL"),
        "kpis": results,
    }

    json_file = args.output_dir / "kpi_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(kpi_report, f, indent=2)
    print(f"\n✓ Saved KPI results to {json_file}")

    # Export flat CSV summary
    summary_rows = [
        {
            "kpi_name": r["kpi_name"],
            "computed_value": r["computed_value"],
            "unit": r["unit"],
            "target_min": r["target_min"],
            "target_max": r["target_max"],
            "status": r["status"],
            "owner": r["owner"],
            "update_frequency": r["update_frequency"],
        }
        for r in results
    ]
    summary_df = pd.DataFrame(summary_rows)
    csv_file = args.output_dir / "kpi_summary.csv"
    summary_df.to_csv(csv_file, index=False)
    print(f"✓ Saved KPI summary to {csv_file}")

    # Export KPI catalogue (definitions only) for documentation
    catalogue_rows = [
        {
            "kpi_name": kpi.name,
            "description": kpi.description,
            "formula": kpi.formula,
            "data_source": "; ".join(kpi.data_source),
            "unit": kpi.unit,
            "target_min": kpi.target_min,
            "target_max": kpi.target_max,
            "owner": kpi.owner,
            "update_frequency": kpi.update_frequency,
        }
        for kpi in KPI_CATALOGUE
    ]
    catalogue_df = pd.DataFrame(catalogue_rows)
    catalogue_file = args.output_dir / "kpi_catalogue.csv"
    catalogue_df.to_csv(catalogue_file, index=False)
    print(f"✓ Saved KPI catalogue to {catalogue_file}")

    # Print executive summary
    print(f"\n{'='*55}")
    print(f"  KPI Report — {kpi_report['passing']}/{kpi_report['total_kpis']} KPIs within target")
    print(f"{'='*55}")
    for r in results:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} {r['kpi_name']}: {r['computed_value']} {r['unit']}")
        if r["deviation_notes"]:
            for note in r["deviation_notes"]:
                print(f"      ⚠ {note}")
    print(f"{'='*55}")
    print("\nKPI computation pipeline completed successfully!")


if __name__ == "__main__":
    main()
