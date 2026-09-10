-- Longitudinal monthly average review score and volume (2017-01 to 2018-08)
SELECT 
    substr(o.order_purchase_timestamp, 1, 7) AS period,
    ROUND(AVG(r.review_score), 2) AS average_review_score,
    COUNT(r.review_score) AS total_reviews
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_purchase_timestamp IS NOT NULL
GROUP BY substr(o.order_purchase_timestamp, 1, 7)
HAVING substr(o.order_purchase_timestamp, 1, 7) >= '2017-01' 
   AND substr(o.order_purchase_timestamp, 1, 7) <= '2018-08'
ORDER BY period ASC;
