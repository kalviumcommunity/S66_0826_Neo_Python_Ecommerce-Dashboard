-- vw_monthly_revenue.sql
-- Single Source of Truth for Monthly Revenue & Order Volume
-- Centralizes monthly financial calculations to prevent metric drift across dashboards.

DROP VIEW IF EXISTS vw_monthly_revenue;

CREATE VIEW vw_monthly_revenue AS
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS active_customers,
    ROUND(SUM(COALESCE(p.payment_value, 0.0)), 2) AS total_revenue,
    ROUND(AVG(COALESCE(p.payment_value, 0.0)), 2) AS avg_order_value,
    ROUND(SUM(CASE WHEN o.order_status = 'delivered' THEN COALESCE(p.payment_value, 0.0) ELSE 0.0 END), 2) AS delivered_revenue
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
GROUP BY strftime('%Y-%m', o.order_purchase_timestamp);
