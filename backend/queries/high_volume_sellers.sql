-- High-Volume Sellers Performance Query
-- Demonstrates WHERE (filtering delivered orders before grouping),
-- GROUP BY (aggregating per seller),
-- HAVING (filtering for sellers with at least 50 orders and average review score < 4.0),
-- and ORDER BY (ranking by total orders descending).
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_sold,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_city, s.seller_state
HAVING COUNT(DISTINCT oi.order_id) >= 50
   AND AVG(r.review_score) < 4.0
ORDER BY total_orders DESC;
