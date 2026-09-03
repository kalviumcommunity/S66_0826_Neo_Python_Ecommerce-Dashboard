-- Unoptimized Seller Analytics Query (Anti-Pattern Demonstration)
-- Antipatterns demonstrated:
-- 1. SELECT * retrieves all columns across 5 joined tables (high I/O, memory overhead).
-- 2. Late filtering: Joins all orders, order_items, sellers, payments, and reviews BEFORE filtering.
-- 3. No CTEs: Monolithic structure with unnecessary row multiplication.

SELECT *
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
LEFT JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01';
