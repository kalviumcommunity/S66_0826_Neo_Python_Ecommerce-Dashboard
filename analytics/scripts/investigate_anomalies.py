"""Investigate unusual Olist order outcomes using a reproducible RCA workflow.

The lesson's generic ``timestamp``, ``success``, and ``error_message`` fields do
not exist in Olist. This workflow uses order purchase timestamps, delivered
orders as an operational success proxy, order statuses as failure evidence,
and payment/customer/product dimensions for segmentation. It does not claim
an external payment-provider incident without external evidence.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

try:
    dataset_dtypes = import_module("scripts.ingest_data").DATASET_DTYPES
except ModuleNotFoundError:  # Supports direct execution from scripts/
    dataset_dtypes = import_module("ingest_data").DATASET_DTYPES

DATASET_DTYPES = dataset_dtypes
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output" / "root_cause"
FIGURE_DIR = OUTPUT_DIR / "figures"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
MIN_OBSERVATIONS = 20
MIN_FALLBACK_OBSERVATIONS = 5


def read_processed(filename: str) -> pd.DataFrame:
    """Read a processed Olist CSV with the project's identifier dtypes."""
    path = PROCESSED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required processed file not found: {path}")
    return pd.read_csv(path, dtype=DATASET_DTYPES.get(filename))


def parse_purchase_timestamp(orders: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Parse the Olist purchase timestamp with an explicit format."""
    original = orders["order_purchase_timestamp"].copy()
    parsed = pd.to_datetime(original, format=TIMESTAMP_FORMAT, errors="coerce")
    invalid = original.notna() & parsed.isna()
    if invalid.any():
        raise ValueError(
            f"Found {int(invalid.sum())} invalid non-empty purchase timestamps: "
            f"{original.loc[invalid].head(5).tolist()}"
        )
    result = orders.copy()
    result["order_purchase_timestamp"] = parsed
    audit = {
        "format": TIMESTAMP_FORMAT,
        "dtype_before": str(original.dtype),
        "dtype_after": str(parsed.dtype),
        "invalid_non_empty_values": int(invalid.sum()),
        "null_values": int(parsed.isna().sum()),
    }
    return result, audit


def aggregate_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """Reduce payment rows to one row per order before joining."""
    return (
        payments.groupby("order_id", as_index=False, dropna=False)
        .agg(
            order_revenue=("payment_value", "sum"),
            payment_record_count=("payment_value", "count"),
            payment_type=("payment_type", lambda values: values.mode().iat[0] if not values.mode().empty else "unknown"),
        )
    )


def aggregate_product_segments(items: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Create one product-category descriptor per order without multiplying rows."""
    item_categories = items[["order_id", "product_id"]].merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    item_categories["product_category_name"] = item_categories[
        "product_category_name"
    ].fillna("unknown")
    return (
        item_categories.groupby("order_id", as_index=False)
        .agg(
            product_category=(
                "product_category_name",
                lambda values: values.mode().iat[0] if not values.mode().empty else "unknown",
            ),
            product_count=("product_id", "nunique"),
        )
    )


def build_order_features(
    orders: pd.DataFrame,
    payments: pd.DataFrame,
    customers: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build an order-grain table for anomaly and segment analysis."""
    parsed_orders, timestamp_audit = parse_purchase_timestamp(orders)
    result = parsed_orders.merge(
        aggregate_payments(payments), on="order_id", how="left", validate="one_to_one"
    )
    result = result.merge(
        customers[["customer_id", "customer_state"]],
        on="customer_id",
        how="left",
        validate="one_to_one",
    )
    result = result.merge(
        aggregate_product_segments(items, products),
        on="order_id",
        how="left",
        validate="one_to_one",
    )
    result["payment_type"] = result["payment_type"].fillna("no_payment_record")
    result["customer_state"] = result["customer_state"].fillna("unknown")
    result["product_category"] = result["product_category"].fillna("unknown")
    result["order_revenue"] = result["order_revenue"].fillna(0)
    result["purchase_date"] = result["order_purchase_timestamp"].dt.date.astype("string")
    result["purchase_hour"] = result["order_purchase_timestamp"].dt.hour
    result["is_successful"] = result["order_status"].eq("delivered")
    result["is_failed"] = result["order_status"].isin(["canceled", "unavailable"])
    result["is_problem_period"] = False
    if not result["order_id"].is_unique:
        raise AssertionError("Order-level feature table contains duplicate order IDs")
    audit = {
        "timestamp": timestamp_audit,
        "orders_before": int(len(orders)),
        "orders_after": int(len(result)),
        "order_ids_unique": bool(result["order_id"].is_unique),
        "payment_rows_aggregated_before_join": int(len(payments)),
    }
    return result, audit


def summarize_outcomes(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Calculate counts, rates, and revenue for a grouping column."""
    summary = (
        frame.groupby(group_column, dropna=False)
        .agg(
            order_count=("order_id", "count"),
            successful_orders=("is_successful", "sum"),
            failed_orders=("is_failed", "sum"),
            revenue=("order_revenue", "sum"),
        )
        .reset_index()
    )
    summary["success_rate"] = summary["successful_orders"] / summary["order_count"]
    summary["failure_rate"] = summary["failed_orders"] / summary["order_count"]
    return summary.sort_values(["failure_rate", "order_count"], ascending=[False, False])


def detect_time_window(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Detect a low-success date and zoom into its lowest-performing hour."""
    daily = summarize_outcomes(orders, "purchase_date")
    daily["revenue"] = daily["revenue"].round(2)
    valid_daily = daily[daily["order_count"] >= MIN_OBSERVATIONS]
    selection_population = valid_daily if not valid_daily.empty else daily[daily["order_count"] >= MIN_FALLBACK_OBSERVATIONS]
    if selection_population.empty:
        selection_population = daily
    threshold = float(selection_population["success_rate"].mean() - selection_population["success_rate"].std())
    anomalies = selection_population[selection_population["success_rate"] < threshold]
    selection_method = "mean_minus_one_standard_deviation"
    if anomalies.empty:
        anomalies = selection_population.nsmallest(5, "success_rate")
        selection_method = "lowest_success_rate_fallback"
    if valid_daily.empty:
        selection_method += "_low_volume_warning"
    problem_date = str(
        anomalies.sort_values(["order_count", "success_rate"], ascending=[False, True])
        .iloc[0]["purchase_date"]
    )

    day_orders = orders[orders["purchase_date"].eq(problem_date)].copy()
    hourly = summarize_outcomes(day_orders, "purchase_hour")
    valid_hourly = hourly[hourly["order_count"] >= MIN_OBSERVATIONS]
    if valid_hourly.empty:
        valid_hourly = hourly[hourly["order_count"] >= MIN_FALLBACK_OBSERVATIONS]
    if valid_hourly.empty:
        valid_hourly = hourly
        selection_method += "_low_volume_hour_warning"
    problem_hour = int(
        valid_hourly.sort_values(["order_count", "success_rate"], ascending=[False, True])
        .iloc[0]["purchase_hour"]
    )
    orders["is_problem_period"] = orders["purchase_date"].eq(problem_date) & orders["purchase_hour"].eq(problem_hour)
    hourly["period"] = hourly["purchase_hour"].map(lambda hour: "problem_hour" if hour == problem_hour else "other_hour")
    before = orders[(orders["purchase_date"].eq(problem_date)) & (orders["purchase_hour"] < problem_hour)]
    during = orders[orders["is_problem_period"]]
    after = orders[(orders["purchase_date"].eq(problem_date)) & (orders["purchase_hour"] > problem_hour)]
    comparison = pd.DataFrame(
        [
            {"period": "before_problem_hour", "order_count": len(before), "success_rate": before["is_successful"].mean(), "failure_rate": before["is_failed"].mean()},
            {"period": "problem_hour", "order_count": len(during), "success_rate": during["is_successful"].mean(), "failure_rate": during["is_failed"].mean()},
            {"period": "after_problem_hour", "order_count": len(after), "success_rate": after["is_successful"].mean(), "failure_rate": after["is_failed"].mean()},
        ]
    )
    details = {
        "problem_date": problem_date,
        "problem_hour": problem_hour,
        "anomaly_threshold": threshold,
        "selection_method": selection_method,
        "minimum_observations": MIN_OBSERVATIONS,
        "minimum_fallback_observations": MIN_FALLBACK_OBSERVATIONS,
        "anomaly_dates": [str(value) for value in anomalies["purchase_date"].tolist()],
        "problem_period_order_count": int(len(during)),
        "problem_period_revenue": float(during["order_revenue"].sum()),
    }
    return daily, pd.concat([hourly.assign(scope="problem_date"), comparison.assign(scope="before_during_after")], ignore_index=True, sort=False), details


def analyze_segments(orders: pd.DataFrame, problem_date: str, problem_hour: int) -> dict[str, pd.DataFrame]:
    """Compare affected segments during the selected date and hour."""
    window = orders[orders["is_problem_period"]].copy()
    dimensions = {
        "payment_type": "payment_type",
        "customer_state": "customer_state",
        "product_category": "product_category",
        "order_status": "order_status",
    }
    return {name: summarize_outcomes(window, column) for name, column in dimensions.items()}


def build_crosstabs(orders: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Create categorical crosstabs for problem versus non-problem periods."""
    output: dict[str, dict[str, Any]] = {}
    for column in ["payment_type", "customer_state", "product_category", "order_status"]:
        counts = pd.crosstab(orders[column], orders["is_problem_period"])
        counts.columns = ["outside_problem_period" if not value else "problem_period" for value in counts.columns]
        percentages = pd.crosstab(orders[column], orders["is_problem_period"], normalize="columns")
        percentages.columns = ["outside_problem_period" if not value else "problem_period" for value in percentages.columns]
        output[column] = {"counts": counts.to_dict(), "column_percentages": percentages.round(4).to_dict()}
    return output


def choose_hypothesis(segments: dict[str, pd.DataFrame], orders: pd.DataFrame) -> dict[str, Any]:
    """Describe the strongest observed pattern without claiming causation."""
    window = orders[orders["is_problem_period"]]
    candidates: list[dict[str, Any]] = []
    for dimension in ["payment_type", "customer_state", "product_category"]:
        table = segments[dimension]
        eligible = table[table["order_count"] >= max(5, MIN_OBSERVATIONS // 4)]
        if eligible.empty:
            continue
        row = eligible.iloc[0]
        baseline = orders[~orders["is_problem_period"]].groupby(dimension)["is_failed"].mean()
        baseline_rate = float(baseline.get(row[dimension], 0.0))
        candidates.append(
            {
                "dimension": dimension,
                "segment": str(row[dimension]),
                "orders": int(row["order_count"]),
                "failed_orders": int(row["failed_orders"]),
                "problem_failure_rate": float(row["failure_rate"]),
                "outside_failure_rate": baseline_rate,
                "rate_difference": float(row["failure_rate"] - baseline_rate),
            }
        )
    candidates.sort(key=lambda item: (item["rate_difference"], item["orders"]), reverse=True)
    strongest = candidates[0] if candidates else None
    if strongest and strongest["rate_difference"] > 0.2 and strongest["orders"] >= 5:
        confidence = "MEDIUM" if strongest["orders"] >= 20 else "LOW"
        statement = (
            f"Failures were concentrated in {strongest['dimension']}={strongest['segment']}; "
            "this suggests a segment-specific operational issue, but does not prove causation."
        )
    else:
        confidence = "INCONCLUSIVE"
        statement = "No sufficiently strong segment concentration was found in the available Olist data."
    return {
        "confidence": confidence,
        "statement": statement,
        "strongest_segment_pattern": strongest,
        "candidate_patterns": candidates,
        "limitations": [
            "Olist contains no application error_message or payment-provider incident log.",
            "Delivered status is an operational fulfillment proxy, not a direct payment-success field.",
            "An observational pattern does not establish a causal relationship.",
        ],
    }


def validate_hypothesis(orders: pd.DataFrame, hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Validate timing, recovery, segment concentration, and external evidence availability."""
    problem = orders[orders["is_problem_period"]]
    outside = orders[~orders["is_problem_period"]]
    strongest = hypothesis["strongest_segment_pattern"]
    checks = {
        "problem_period_has_orders": bool(len(problem) > 0),
        "problem_period_failure_rate": float(problem["is_failed"].mean()) if len(problem) else None,
        "outside_period_failure_rate": float(outside["is_failed"].mean()) if len(outside) else None,
        "segment_pattern_present": bool(strongest),
        "external_event_validation": "not performed; no external event file supplied",
    }
    if strongest:
        checks["segment_failure_rate_exceeds_outside_rate"] = bool(strongest["rate_difference"] > 0)
    checks["conclusion"] = (
        "Pattern is supported by internal timing/segment evidence; external cause is unconfirmed."
        if checks["problem_period_has_orders"] and checks.get("segment_failure_rate_exceeds_outside_rate", False)
        else "Root cause remains unconfirmed; collect logs or external incident evidence before acting."
    )
    return checks


def json_safe(value: Any) -> Any:
    """Convert pandas/numpy scalar values into JSON-compatible values."""
    if pd.isna(value) if not isinstance(value, (dict, list, tuple)) else False:
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def save_outputs(
    daily: pd.DataFrame,
    hourly: pd.DataFrame,
    segments: dict[str, pd.DataFrame],
    crosstabs: dict[str, dict[str, Any]],
    report: dict[str, Any],
) -> None:
    """Write tabular, JSON, text, and visual RCA outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT_DIR / "daily_anomaly_metrics.csv", index=False)
    hourly.to_csv(OUTPUT_DIR / "hourly_problem_window.csv", index=False)
    for name, table in segments.items():
        table.to_csv(OUTPUT_DIR / f"segment_{name}.csv", index=False)
    with (OUTPUT_DIR / "failure_crosstabs.json").open("w", encoding="utf-8") as handle:
        json.dump(crosstabs, handle, indent=2, default=json_safe)
    with (OUTPUT_DIR / "investigation_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=json_safe)

    hypothesis = report["hypothesis"]
    details = report["time_window"]
    text = f"""ROOT CAUSE INVESTIGATION REPORT
{'=' * 70}

OBSERVATION
- Problem date: {details['problem_date']}
- Problem hour: {details['problem_hour']}:00-{details['problem_hour'] + 1}:00 (dataset-local timestamp)
- Orders in problem hour: {details['problem_period_order_count']:,}
- Revenue in problem hour: {details['problem_period_revenue']:,.2f}
- Detection method: {details['selection_method']}

ANALYSIS
- Olist operational success proxy: order_status == 'delivered'
- Failed statuses: canceled and unavailable
- Strongest pattern: {hypothesis.get('statement')}

HYPOTHESIS (Confidence: {hypothesis['confidence']})
{hypothesis['statement']}

EVIDENCE LIMITATIONS
- No application error logs or payment-provider incident data are included in Olist.
- Correlation and segment concentration do not prove causation.

RECOMMENDED ACTIONS
1. Compare this period with payment gateway and application logs if available.
2. Add monitoring for hourly cancellation/unavailable spikes by payment type.
3. Investigate any segment with a sustained elevated failure rate.
4. Do not implement a causal fix until external or operational evidence confirms it.

VALIDATION
{report['validation']['conclusion']}
"""
    (OUTPUT_DIR / "investigation_report.txt").write_text(text, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily["purchase_date"].astype(str), daily["success_rate"], marker=".", linewidth=1)
    ax.set(title="Daily Olist Operational Success Rate", xlabel="Purchase date", ylabel="Success rate")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "daily_success_rate.png", dpi=150)
    plt.close(fig)

    payment = segments["payment_type"].sort_values("failure_rate", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(payment["payment_type"].astype(str), payment["failure_rate"])
    ax.set(title="Problem-Period Failure Rate by Payment Type", xlabel="Payment type", ylabel="Failure rate")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "segment_failure_rates.png", dpi=150)
    plt.close(fig)


def run_workflow() -> dict[str, Any]:
    """Run the complete root-cause investigation workflow."""
    orders = read_processed("olist_orders_dataset.csv")
    payments = read_processed("olist_order_payments_dataset.csv")
    customers = read_processed("olist_customers_dataset.csv")
    items = read_processed("olist_order_items_dataset.csv")
    products = read_processed("olist_products_dataset.csv")
    order_features, build_audit = build_order_features(orders, payments, customers, items, products)
    daily, hourly, time_window = detect_time_window(order_features)
    segments = analyze_segments(order_features, time_window["problem_date"], time_window["problem_hour"])
    crosstabs = build_crosstabs(order_features)
    hypothesis = choose_hypothesis(segments, order_features)
    validation = validate_hypothesis(order_features, hypothesis)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "data/processed/",
        "build_audit": build_audit,
        "time_window": time_window,
        "hypothesis": hypothesis,
        "validation": validation,
        "available_error_log_evidence": False,
        "external_validation": "not performed; no external event file supplied",
        "recommended_next_evidence": [
            "payment gateway logs",
            "application error logs",
            "deployment and infrastructure incident logs",
        ],
    }
    save_outputs(daily, hourly, segments, crosstabs, report)
    print("\n" + "=" * 70)
    print("ROOT CAUSE INVESTIGATION COMPLETE")
    print("=" * 70)
    print(f"Problem date: {time_window['problem_date']}")
    print(f"Problem hour: {time_window['problem_hour']}:00")
    print(f"Problem-period orders: {time_window['problem_period_order_count']:,}")
    print(f"Hypothesis confidence: {hypothesis['confidence']}")
    print(f"Reports saved to {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_workflow()


if __name__ == "__main__":
    main()
