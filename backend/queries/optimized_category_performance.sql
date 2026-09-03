-- Optimized Category Performance Query
-- Optimization Techniques Applied:
-- 1. Explicit Column Selection: Only projects category_name, total_orders, items_count, and revenue.
-- 2. Early Filtering: Filters delivered orders within the 1-year window first.
-- 3. CTE Pipeline: Separates order filtering, item enrichment, and dimensional aggregation.

WITH target_orders AS (
    -- Early filter: Only delivered orders in the 1-year window
    SELECT
        order_id
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp >= '2017-06-01'
      AND order_purchase_timestamp <= '2018-06-01'
),

category_order_items AS (
    -- Join filtered orders with items and product categories projecting strictly required fields
    SELECT
        t.product_category_name_english AS category_name,
        oi.order_id,
        oi.price,
        oi.freight_value
    FROM target_orders to_orders
    JOIN order_items oi ON to_orders.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
)

-- Final Aggregation: Group by category with clean metrics and sorted by revenue
SELECT
    category_name,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(price), 2) AS total_revenue,
    ROUND(AVG(price), 2) AS avg_item_price,
    ROUND(SUM(freight_value), 2) AS total_freight
FROM category_order_items
GROUP BY category_name
HAVING COUNT(DISTINCT order_id) >= 50
ORDER BY total_revenue DESC;
