"""Build a complete, auditable Olist order-item integration."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = DATA / "integrated"


def load(filename):
    return pd.read_csv(DATA / filename)


def main():
    customers = load("olist_customers_dataset.csv")
    orders = load("olist_orders_dataset.csv")
    items = load("olist_order_items_dataset.csv")
    products = load("olist_products_dataset.csv")
    translations = load("product_category_name_translation.csv")
    sellers = load("olist_sellers_dataset.csv")
    payments = load("olist_order_payments_dataset.csv")
    reviews = load("olist_order_reviews_dataset.csv")

    payment_totals = payments.groupby("order_id", as_index=False).agg(
        total_payment_value=("payment_value", "sum"),
        payment_record_count=("payment_sequential", "count"),
    )
    review_summary = reviews.groupby("order_id", as_index=False).agg(
        review_score=("review_score", "mean"),
        review_count=("review_id", "nunique"),
    )

    result = (orders.merge(customers, on="customer_id", how="left", validate="many_to_one")
        .merge(items, on="order_id", how="left", validate="one_to_many")
        .merge(products, on="product_id", how="left", validate="many_to_one")
        .merge(translations, on="product_category_name", how="left", validate="many_to_one")
        .merge(sellers, on="seller_id", how="left", validate="many_to_one")
        .merge(payment_totals, on="order_id", how="left", validate="many_to_one")
        .merge(review_summary, on="order_id", how="left", validate="many_to_one"))

    orders_without_items_removed = int(result["order_item_id"].isna().sum())
    result = result.loc[result["order_item_id"].notna()].copy()
    result["has_product"] = result["product_id"].notna()
    result["has_seller"] = result["seller_id"].notna()
    result["has_payment"] = result["total_payment_value"].notna()
    result["has_review"] = result["review_score"].notna()
    result["item_revenue"] = result["price"].fillna(0) + result["freight_value"].fillna(0)
    result["product_category_name_english"] = result["product_category_name_english"].fillna("unknown")

    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "customer_order_item_view.csv"
    result.to_csv(output, index=False, encoding="utf-8")

    audit = pd.DataFrame([
        {"check": "source_order_rows", "value": len(orders)},
        {"check": "source_order_item_rows", "value": len(items)},
        {"check": "orders_without_items_removed", "value": orders_without_items_removed},
        {"check": "integrated_rows", "value": len(result)},
        {"check": "integrated_distinct_orders", "value": result["order_id"].nunique()},
        {"check": "integrated_distinct_unique_customers", "value": result["customer_unique_id"].nunique()},
        {"check": "missing_product_rows", "value": int(result["product_id"].isna().sum())},
        {"check": "missing_seller_rows", "value": int(result["seller_id"].isna().sum())},
        {"check": "missing_payment_rows", "value": int(result["total_payment_value"].isna().sum())},
        {"check": "missing_review_rows", "value": int(result["review_score"].isna().sum())},
    ])
    audit.to_csv(OUT / "customer_order_item_view_audit.csv", index=False, encoding="utf-8")

    print(f"Created {output.relative_to(ROOT)}")
    print(f"Rows: {len(result):,} (one row per order item)")
    print(f"Distinct orders: {result['order_id'].nunique():,}")
    print(f"Distinct unique customers: {result['customer_unique_id'].nunique():,}")
    print(f"Audit: {(OUT / 'customer_order_item_view_audit.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
