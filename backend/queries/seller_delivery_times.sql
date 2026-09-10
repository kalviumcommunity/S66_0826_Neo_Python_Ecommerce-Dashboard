-- Fetch delivered order purchase and delivery timestamps for a specific seller
SELECT 
    o.order_delivered_customer_date, 
    o.order_purchase_timestamp
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE oi.seller_id = :seller_id
  AND o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_purchase_timestamp IS NOT NULL;
