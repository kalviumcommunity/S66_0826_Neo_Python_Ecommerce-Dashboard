-- Monthly historical risk and delivery metrics per seller for sparklines
WITH seller_monthly_orders AS (
    SELECT 
        oi.seller_id,
        substr(o.order_purchase_timestamp, 1, 7) AS period,
        o.order_id,
        o.order_status,
        CASE WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
        CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY oi.seller_id, substr(o.order_purchase_timestamp, 1, 7), o.order_id, o.order_status, o.order_delivered_customer_date, o.order_estimated_delivery_date
),
seller_monthly_reviews AS (
    SELECT 
        smo.seller_id,
        smo.period,
        COUNT(DISTINCT r.review_id) AS review_count,
        AVG(r.review_score) AS avg_review,
        SUM(CASE WHEN r.review_score IN (1, 2) THEN 1 ELSE 0 END) AS low_review_count
    FROM seller_monthly_orders smo
    JOIN order_reviews r ON smo.order_id = r.order_id
    GROUP BY smo.seller_id, smo.period
),
monthly_agg AS (
    SELECT 
        smo.seller_id,
        smo.period,
        COUNT(DISTINCT smo.order_id) AS orders,
        SUM(CASE WHEN smo.order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders,
        SUM(smo.is_late) AS late_deliveries,
        SUM(smo.is_canceled) AS canceled_orders
    FROM seller_monthly_orders smo
    GROUP BY smo.seller_id, smo.period
)
SELECT 
    ma.seller_id,
    ma.period,
    ma.orders,
    ma.delivered_orders,
    ma.late_deliveries,
    ma.canceled_orders,
    COALESCE(smr.review_count, 0) AS review_count,
    COALESCE(smr.avg_review, 4.09) AS avg_review,
    COALESCE(smr.low_review_count, 0) AS low_review_count
FROM monthly_agg ma
LEFT JOIN seller_monthly_reviews smr ON ma.seller_id = smr.seller_id AND ma.period = smr.period
ORDER BY ma.period ASC;
