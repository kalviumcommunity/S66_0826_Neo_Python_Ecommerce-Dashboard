"""GroupBy aggregation, segment insights, and JSON reports."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "integrated" / "customer_order_item_view.csv"
OUT = ROOT / "output" / "segment_analysis"


def number(value):
    return None if pd.isna(value) else round(float(value), 2)


def main() -> None:
    df = pd.read_csv(INPUT, parse_dates=["order_purchase_timestamp"])
    OUT.mkdir(parents=True, exist_ok=True)
    orders = df.groupby("order_id", as_index=False).agg(
        customer_unique_id=("customer_unique_id", "first"),
        customer_id=("customer_id", "first"),
        order_purchase_timestamp=("order_purchase_timestamp", "first"),
        order_revenue=("item_revenue", "sum"),
        review_score=("review_score", "mean"),
    )
    order_counts = orders.groupby("customer_unique_id").size()
    last_purchase = orders.groupby("customer_unique_id")["order_purchase_timestamp"].max()
    customer = orders.groupby("customer_unique_id", as_index=False).agg(
        customer_id=("customer_id", "first"), total_revenue=("order_revenue", "sum"),
        customer_count=("order_id", "nunique"), avg_review_score=("review_score", "mean"),
    )
    customer["order_count"] = customer["customer_unique_id"].map(order_counts)
    customer["last_purchase_timestamp"] = customer["customer_unique_id"].map(last_purchase)
    customer["days_since_last_purchase"] = (orders["order_purchase_timestamp"].max() - customer["last_purchase_timestamp"]).dt.days
    customer["churn"] = customer["days_since_last_purchase"] >= 90
    customer["customer_type"] = pd.cut(customer["order_count"], [0, 1, 3, float("inf")], labels=["one_time", "repeat", "loyal"]).astype(str)

    # Named aggregations keep the output schema explicit and order-independent.
    segment_metrics = customer.groupby("customer_type", observed=True).agg(
        churn_rate=("churn", "mean"),
        total_revenue=("total_revenue", "sum"),
        customer_count=("customer_id", "count"),
        avg_review_score=("avg_review_score", "mean"),
    )
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(ascending=False, method="dense")
    segment_metrics["revenue_contribution"] = segment_metrics["total_revenue"] / segment_metrics["total_revenue"].sum() * 100
    segment_metrics.to_csv(OUT / "segment_metrics.csv")

    item = df.merge(customer[["customer_unique_id", "customer_type"]], on="customer_unique_id", how="left")
    item["product"] = item["product_category_name_english"].fillna("unknown")
    product_segment = item.groupby(["customer_type", "product"], observed=True).agg(
        total_revenue=("item_revenue", "sum"), customer_count=("customer_unique_id", "nunique")
    )
    product_segment.to_csv(OUT / "product_segment.csv")
    product_segment["total_revenue"].unstack(fill_value=0).to_csv(OUT / "revenue_pivot.csv")
    product_segment["customer_count"].unstack(fill_value=0).to_csv(OUT / "customer_count_pivot.csv")

    insights = []
    for segment, row in segment_metrics.sort_values("churn_rate", ascending=False).iterrows():
        action = "HIGH PRIORITY: investigate inactivity drivers and retention offers." if row["churn_rate"] > .10 else "Healthy: maintain current retention service level." if row["churn_rate"] < .02 else "Monitor: improve repeat purchase conversion."
        insights.append({"segment": segment, "customer_count": int(row["customer_count"]), "churn_rate": f'{row["churn_rate"]:.1%}', "total_revenue": f'${row["total_revenue"]:.0f}', "revenue_contribution": f'{row["revenue_contribution"]:.1f}%', "action": action})
    pd.DataFrame(insights).to_csv(ROOT / "output" / "segment_insights.csv", index=False)

    segments = {}
    for segment, row in segment_metrics.iterrows():
        products = {str(product): {"revenue": number(product_row["total_revenue"]), "customer_count": int(product_row["customer_count"])} for product, product_row in product_segment.loc[segment].iterrows()}
        segments[str(segment)] = {"churn_proxy_rate": number(row["churn_rate"]), "total_revenue": number(row["total_revenue"]), "customer_count": int(row["customer_count"]), "revenue_contribution_percent": number(row["revenue_contribution"]), "products": products}
    report = {"report": "Revenue and Product Segment Analysis", "revenue_measure": "item_revenue (price + freight_value)", "churn_definition": "customer inactive for at least 90 days after last purchase", "customer_segment_definition": {"one_time": "1 order", "repeat": "2 to 3 orders", "loyal": "more than 3 orders"}, "segments": segments}
    with (OUT / "segment_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("Saved CSV and JSON segment reports")


if __name__ == "__main__":
    main()
