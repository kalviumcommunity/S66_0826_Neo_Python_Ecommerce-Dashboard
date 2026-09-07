-- validation_monthly_revenue_metrics.sql
-- Monthly financial metrics computed via SQL for cross-layer parity comparison with Pandas.

SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(COALESCE(p.payment_value, 0.0)), 2) AS total_revenue,
    ROUND(AVG(COALESCE(p.payment_value, 0.0)), 2) AS avg_payment_value
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
GROUP BY strftime('%Y-%m', o.order_purchase_timestamp)
ORDER BY order_month ASC;
