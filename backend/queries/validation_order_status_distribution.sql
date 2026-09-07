-- validation_order_status_distribution.sql
-- Aggregates orders by status for cross-layer computational parity check against Python.

SELECT
    order_status,
    COUNT(order_id) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC, order_status ASC;
