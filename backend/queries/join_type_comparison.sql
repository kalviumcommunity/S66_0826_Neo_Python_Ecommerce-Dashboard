-- Join Type Row Count & Key Cardinality Comparison Query
-- Compares row counts and distinct key matches for INNER JOIN vs LEFT JOIN semantics.
SELECT
    'customers_to_orders' AS join_scenario,
    'INNER JOIN' AS join_type,
    COUNT(*) AS result_rows,
    COUNT(DISTINCT c.customer_id) AS distinct_left_keys,
    COUNT(DISTINCT o.order_id) AS distinct_right_keys
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id

UNION ALL

SELECT
    'customers_to_orders' AS join_scenario,
    'LEFT JOIN' AS join_type,
    COUNT(*) AS result_rows,
    COUNT(DISTINCT c.customer_id) AS distinct_left_keys,
    COUNT(DISTINCT o.order_id) AS distinct_right_keys
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id

UNION ALL

SELECT
    'orders_to_order_items' AS join_scenario,
    'INNER JOIN (1:N multiplicity)' AS join_type,
    COUNT(*) AS result_rows,
    COUNT(DISTINCT o.order_id) AS distinct_left_keys,
    COUNT(DISTINCT oi.order_item_id) AS distinct_right_keys
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id

UNION ALL

SELECT
    'orders_to_order_items' AS join_scenario,
    'LEFT JOIN (1:N multiplicity)' AS join_type,
    COUNT(*) AS result_rows,
    COUNT(DISTINCT o.order_id) AS distinct_left_keys,
    COUNT(DISTINCT oi.order_item_id) AS distinct_right_keys
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id;
