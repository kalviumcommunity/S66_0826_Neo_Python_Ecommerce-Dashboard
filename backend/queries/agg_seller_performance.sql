-- agg_seller_performance.sql
-- Pre-aggregated summary table for seller risk and operational metrics.
-- Includes order volume, delayed delivery count, average review score, and freshness timestamp.

DROP TABLE IF EXISTS agg_seller_performance;

CREATE TABLE agg_seller_performance AS
SELECT
    s.seller_id,
    s.seller_state,
    s.seller_city,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_sold,
    ROUND(SUM(COALESCE(oi.price, 0.0)), 2) AS total_merchandise_value,
    ROUND(SUM(COALESCE(oi.freight_value, 0.0)), 2) AS total_freight_value,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_deliveries_count,
    ROUND(AVG(COALESCE(r.review_score, 0.0)), 2) AS avg_review_score,
    CURRENT_TIMESTAMP AS updated_at
FROM sellers s
INNER JOIN order_items oi ON s.seller_id = oi.seller_id
INNER JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN (
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
) r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_state, s.seller_city;

CREATE INDEX IF NOT EXISTS idx_agg_seller_perf_seller ON agg_seller_performance(seller_id);
CREATE INDEX IF NOT EXISTS idx_agg_seller_perf_state ON agg_seller_performance(seller_state);
