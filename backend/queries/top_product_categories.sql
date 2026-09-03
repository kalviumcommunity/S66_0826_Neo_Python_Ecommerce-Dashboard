-- Top Product Categories by Revenue Query
-- Demonstrates WHERE (filtering non-null categories and delivered orders),
-- GROUP BY (aggregating per product category),
-- HAVING (filtering categories with total revenue >= 50,000 BRL),
-- and ORDER BY (sorting by total revenue descending).
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category_name,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_sold,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS avg_item_price,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_value
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
  AND p.product_category_name IS NOT NULL
GROUP BY category_name
HAVING SUM(oi.price) >= 50000.0
ORDER BY total_revenue DESC;
