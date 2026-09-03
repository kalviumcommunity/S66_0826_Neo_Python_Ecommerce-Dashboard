-- Comprehensive Multi-Table Relational JOIN
-- Combines customers, orders, order_items, payments, and reviews.
-- Demonstrates relational joins across 5 tables with item-level aggregation.
SELECT
    o.order_id,
    c.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    COUNT(DISTINCT oi.order_item_id) AS total_items,
    ROUND(SUM(oi.price), 2) AS total_item_price,
    ROUND(SUM(oi.freight_value), 2) AS total_freight,
    ROUND(AVG(p.payment_value), 2) AS avg_payment_record_value,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN order_payments p ON o.order_id = p.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
GROUP BY
    o.order_id,
    c.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp
LIMIT 1000;
