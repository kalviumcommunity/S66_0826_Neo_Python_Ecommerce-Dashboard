-- vw_active_customers.sql
-- Single Source of Truth for Active Customers and Geographic Spread
-- Defines customer engagement metric to avoid departmental divergence.

DROP VIEW IF EXISTS vw_active_customers;

CREATE VIEW vw_active_customers AS
SELECT
    c.customer_state,
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT c.customer_unique_id) AS distinct_active_customers,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(COALESCE(p.payment_value, 0.0)), 2) AS total_customer_spend
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM order_payments
    GROUP BY order_id
) p ON o.order_id = p.order_id
WHERE o.order_status != 'canceled'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY c.customer_state, strftime('%Y-%m', o.order_purchase_timestamp);
