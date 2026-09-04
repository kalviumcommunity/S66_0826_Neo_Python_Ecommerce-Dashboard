-- validation_seller_kpis.sql
-- Seller-level order and review metrics computed via SQL for cross-layer parity verification.

SELECT
    s.seller_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(SUM(COALESCE(oi.price, 0.0)), 2) AS total_sales,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM sellers s
INNER JOIN order_items oi ON s.seller_id = oi.seller_id
INNER JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN (
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
) r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id
ORDER BY total_orders DESC, total_sales DESC
LIMIT 200;
