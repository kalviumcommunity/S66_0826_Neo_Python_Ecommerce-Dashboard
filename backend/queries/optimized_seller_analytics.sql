-- Optimized Seller Analytics Query
-- Optimization Techniques Applied:
-- 1. Explicit Column Selection: Only projects required metrics, eliminating SELECT * payload.
-- 2. Early Filtering (WHERE before JOIN): Prunes orders to delivered/in-range BEFORE joining.
-- 3. Common Table Expressions (CTEs): Breaks down complex logic into isolated, readable, pre-aggregated stages.

WITH filtered_orders AS (
    -- Early filter: Prune orders table to only qualifying delivered orders within date bounds
    SELECT
        order_id,
        order_purchase_timestamp
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp >= '2017-01-01'
      AND order_purchase_timestamp < '2018-09-01'
),

filtered_order_items AS (
    -- Join order_items ONLY with already-filtered orders to avoid joining full dataset
    SELECT
        oi.seller_id,
        oi.order_id,
        oi.price,
        oi.freight_value
    FROM order_items oi
    JOIN filtered_orders fo ON oi.order_id = fo.order_id
),

seller_order_reviews AS (
    -- Pre-aggregate review scores per order to prevent 1:N fanout prior to seller rollup
    SELECT
        order_id,
        AVG(review_score) AS avg_order_review
    FROM order_reviews
    GROUP BY order_id
),

seller_performance_aggregates AS (
    -- Aggregate metrics at seller level
    SELECT
        foi.seller_id,
        COUNT(DISTINCT foi.order_id) AS total_orders,
        COUNT(foi.order_id) AS total_items_sold,
        ROUND(SUM(foi.price), 2) AS total_revenue,
        ROUND(AVG(foi.price), 2) AS avg_item_price,
        ROUND(SUM(foi.freight_value), 2) AS total_freight,
        ROUND(AVG(sor.avg_order_review), 2) AS avg_seller_review
    FROM filtered_order_items foi
    LEFT JOIN seller_order_reviews sor ON foi.order_id = sor.order_id
    GROUP BY foi.seller_id
)

-- Final Projection: Join aggregated performance metrics with seller metadata
SELECT
    spa.seller_id,
    s.seller_city,
    s.seller_state,
    spa.total_orders,
    spa.total_items_sold,
    spa.total_revenue,
    spa.avg_item_price,
    spa.total_freight,
    spa.avg_seller_review
FROM seller_performance_aggregates spa
JOIN sellers s ON spa.seller_id = s.seller_id
ORDER BY spa.total_revenue DESC;
