-- Order Lifecycle Conversion & Fulfillment Rates Metric
-- Uses CASE statements to categorize order statuses and compute fulfillment, delivery, and cancellation percentages.
SELECT
    strftime('%Y-%m', order_purchase_timestamp) AS year_month,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
    SUM(CASE WHEN order_status = 'shipped' THEN 1 ELSE 0 END) AS shipped_orders,
    SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS canceled_orders,
    SUM(CASE WHEN order_status = 'unavailable' THEN 1 ELSE 0 END) AS unavailable_orders,
    ROUND(CAST(SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS fulfillment_rate_pct,
    ROUND(CAST(SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS cancellation_rate_pct
FROM orders
WHERE order_purchase_timestamp IS NOT NULL
GROUP BY year_month
ORDER BY year_month ASC;
