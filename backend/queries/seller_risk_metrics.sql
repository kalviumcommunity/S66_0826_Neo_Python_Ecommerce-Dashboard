-- Aggregate order status, delivery timeliness, reviews, and revenue per seller
WITH seller_orders AS (
    SELECT 
        oi.seller_id,
        o.order_id,
        o.order_status,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        CASE WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
        CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    GROUP BY oi.seller_id, o.order_id, o.order_status, o.order_delivered_customer_date, o.order_estimated_delivery_date
),
seller_reviews AS (
    SELECT 
        oi.seller_id,
        COUNT(r.review_score) AS review_count,
        AVG(r.review_score) AS avg_review
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN order_reviews r ON o.order_id = r.order_id
    GROUP BY oi.seller_id
),
seller_revenue AS (
    SELECT 
        oi.seller_id,
        COUNT(oi.order_item_id) AS total_items_sold,
        SUM(oi.price) AS total_revenue
    FROM order_items oi
    GROUP BY oi.seller_id
),
seller_agg AS (
    SELECT 
        so.seller_id,
        COUNT(DISTINCT so.order_id) AS total_orders,
        SUM(CASE WHEN so.order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
        SUM(so.is_late) AS late_orders,
        SUM(so.is_canceled) AS canceled_orders
    FROM seller_orders so
    GROUP BY so.seller_id
)
SELECT 
    s.seller_id,
    COALESCE(s.seller_city, 'unknown') AS city,
    COALESCE(s.seller_state, 'unknown') AS state,
    COALESCE(sa.total_orders, 0) AS total_orders,
    COALESCE(sa.delivered_orders, 0) AS delivered_orders,
    COALESCE(sa.late_orders, 0) AS late_orders,
    COALESCE(sa.canceled_orders, 0) AS canceled_orders,
    COALESCE(sr.review_count, 0) AS review_count,
    COALESCE(sr.avg_review, 4.09) AS raw_avg_review,
    COALESCE(srev.total_items_sold, 0) AS total_items_sold,
    COALESCE(srev.total_revenue, 0.0) AS total_revenue
FROM sellers s
LEFT JOIN seller_agg sa ON s.seller_id = sa.seller_id
LEFT JOIN seller_reviews sr ON s.seller_id = sr.seller_id
LEFT JOIN seller_revenue srev ON s.seller_id = srev.seller_id;
