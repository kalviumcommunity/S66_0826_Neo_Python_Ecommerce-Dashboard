-- Category level metrics: seller count, total orders, average review, and delay rate
SELECT 
    COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown') AS category,
    COUNT(DISTINCT oi.seller_id) AS total_sellers,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(
        (SUM(CASE WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1.0 ELSE 0.0 END) / 
         NULLIF(SUM(CASE WHEN o.order_status = 'delivered' THEN 1.0 ELSE 0.0 END), 0)) * 100.0, 
        2
    ) AS late_delivery_rate
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status != 'canceled'
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown')
HAVING COUNT(DISTINCT oi.seller_id) >= 5
ORDER BY total_orders DESC;
