-- Monthly Order & Revenue Threshold Query
-- Demonstrates WHERE (filtering valid purchase timestamps and delivered orders),
-- GROUP BY (aggregating by year-month),
-- HAVING (filtering for mature operating months with at least 1,000 orders and revenue >= 150,000 BRL),
-- and ORDER BY (chronological ordering).
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS year_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS total_customers,
    ROUND(SUM(p.payment_value), 2) AS total_revenue,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_purchase_timestamp IS NOT NULL
  AND o.order_status = 'delivered'
GROUP BY year_month
HAVING COUNT(DISTINCT o.order_id) >= 1000
   AND SUM(p.payment_value) >= 150000.0
ORDER BY year_month ASC;
