-- Delivery performance buckets for one seller, compared with the estimated delivery date.
SELECT
    CASE
        WHEN julianday(o.order_delivered_customer_date) < julianday(o.order_estimated_delivery_date) THEN 'Early'
        WHEN julianday(o.order_delivered_customer_date) = julianday(o.order_estimated_delivery_date) THEN 'On-Time'
        WHEN julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) <= 3 THEN '1-3 Days Late'
        WHEN julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) <= 7 THEN '4-7 Days Late'
        ELSE '>7 Days Late'
    END AS range,
    COUNT(DISTINCT o.order_id) AS count
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE oi.seller_id = :seller_id
  AND o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY range
ORDER BY CASE range
    WHEN 'Early' THEN 1
    WHEN 'On-Time' THEN 2
    WHEN '1-3 Days Late' THEN 3
    WHEN '4-7 Days Late' THEN 4
    ELSE 5
END;
