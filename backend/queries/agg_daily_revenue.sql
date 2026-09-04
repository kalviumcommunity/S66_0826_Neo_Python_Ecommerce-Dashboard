-- agg_daily_revenue.sql
-- Pre-aggregated summary table for instant dashboard rendering.
-- Stores precomputed daily revenue, order volume, and freight metrics with freshness tracking.

DROP TABLE IF EXISTS agg_daily_revenue;

CREATE TABLE agg_daily_revenue AS
SELECT
    DATE(o.order_purchase_timestamp) AS order_date,
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS total_customers,
    ROUND(SUM(COALESCE(p.payment_value, 0.0)), 2) AS daily_revenue,
    ROUND(SUM(CASE WHEN o.order_status = 'delivered' THEN COALESCE(p.payment_value, 0.0) ELSE 0.0 END), 2) AS delivered_revenue,
    ROUND(AVG(COALESCE(p.payment_value, 0.0)), 2) AS avg_order_value,
    CURRENT_TIMESTAMP AS updated_at
FROM orders o
LEFT JOIN (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM order_payments
    GROUP BY order_id
) p ON o.order_id = p.order_id
WHERE o.order_purchase_timestamp IS NOT NULL
  AND o.order_status != 'canceled'
GROUP BY DATE(o.order_purchase_timestamp);

CREATE INDEX IF NOT EXISTS idx_agg_daily_revenue_date ON agg_daily_revenue(order_date);
CREATE INDEX IF NOT EXISTS idx_agg_daily_revenue_month ON agg_daily_revenue(order_month);
