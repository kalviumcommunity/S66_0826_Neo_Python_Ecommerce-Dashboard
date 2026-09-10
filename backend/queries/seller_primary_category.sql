-- Determine the primary category for each seller based on item frequency
WITH seller_cat AS (
    SELECT 
        oi.seller_id,
        COALESCE(t.product_category_name_english, p.product_category_name, 'other') AS category,
        COUNT(*) as cat_count,
        ROW_NUMBER() OVER (
            PARTITION BY oi.seller_id 
            ORDER BY COUNT(*) DESC
        ) as rn
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
    GROUP BY oi.seller_id, COALESCE(t.product_category_name_english, p.product_category_name, 'other')
)
SELECT seller_id, category 
FROM seller_cat 
WHERE rn = 1;
