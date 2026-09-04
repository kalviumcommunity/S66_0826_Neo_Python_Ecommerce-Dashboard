-- Unoptimized Category Performance Query (Anti-Pattern Demonstration)
-- Antipatterns demonstrated:
-- 1. SELECT * with redundant columns across 4 tables.
-- 2. Late filtering: Joins all orders, items, products, and categories BEFORE filtering for delivered status.
-- 3. Complex unreadable subquery nesting instead of structured CTEs.

SELECT *
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-06-01'
  AND o.order_purchase_timestamp <= '2018-06-01';
