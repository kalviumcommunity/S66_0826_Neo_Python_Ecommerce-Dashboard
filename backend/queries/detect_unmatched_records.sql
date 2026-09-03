-- Unmatched Keys & Orphan Detection Query
-- Uses LEFT JOIN with WHERE right_table.key IS NULL to identify records missing relational links.
SELECT
    'customers_without_orders' AS issue_type,
    c.customer_id AS entity_id,
    c.customer_unique_id AS secondary_id,
    'customers' AS source_table
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL

UNION ALL

SELECT
    'orders_without_payments' AS issue_type,
    o.order_id AS entity_id,
    o.customer_id AS secondary_id,
    'orders' AS source_table
FROM orders o
LEFT JOIN order_payments p ON o.order_id = p.order_id
WHERE p.order_id IS NULL;
