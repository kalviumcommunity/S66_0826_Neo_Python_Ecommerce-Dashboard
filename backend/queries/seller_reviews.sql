-- Recent reviews attributed to one seller for the investigation panel.
SELECT
    r.review_id,
    r.order_id,
    r.review_score,
    r.review_comment_message,
    r.review_creation_date,
    COALESCE(t.product_category_name_english, p.product_category_name, 'other') AS product_category
FROM order_items oi
JOIN order_reviews r ON r.order_id = oi.order_id
LEFT JOIN products p ON p.product_id = oi.product_id
LEFT JOIN product_category_name_translation t ON t.product_category_name = p.product_category_name
WHERE oi.seller_id = :seller_id
GROUP BY r.review_id, r.order_id
ORDER BY r.review_creation_date DESC
LIMIT 50;
