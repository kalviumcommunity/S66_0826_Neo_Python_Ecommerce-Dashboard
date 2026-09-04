-- Monthly Active Users (MAU) Metric
-- Computes the monthly count of distinct active customers and order volume over time.
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS year_month,
    COUNT(DISTINCT c.customer_unique_id) AS monthly_active_users,
    COUNT(DISTINCT o.order_id) AS total_orders
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_purchase_timestamp IS NOT NULL
GROUP BY year_month
ORDER BY year_month ASC;
