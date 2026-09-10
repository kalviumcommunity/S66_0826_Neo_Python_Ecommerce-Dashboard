# Data Dictionary

## Dataset Overview

This dataset contains historical Brazilian e-commerce marketplace data from Olist. It includes customers, orders, products, sellers, payments, reviews, delivery dates, and geographic reference data.

The raw files are stored under `data/raw/`. They are a static historical dataset rather than a live daily CRM extract. Monetary values are recorded in Brazilian reais (BRL).

### Source Files

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

## Columns

The complete column-level dictionary is maintained in [`data_dictionary.csv`](data_dictionary.csv). It documents all 45 unique source columns (52 physical fields across the raw files), their technical types, business meaning, examples, KPIs, and constraints.

### Key identifiers

- `order_id`: Order-level join key shared by orders, order items, payments, and reviews.
- `customer_id`: Customer record associated with an order.
- `customer_unique_id`: Persistent shopper identity used for repeat-customer and lifetime-value analysis.
- `product_id`: Product join key shared by order items and product attributes.
- `seller_id`: Seller join key shared by order items and seller attributes.

### Important measures and dates

- `price`: Item merchandise price in BRL.
- `freight_value`: Item-level freight charge in BRL.
- `payment_value`: Amount recorded for one payment record in BRL.
- `order_purchase_timestamp`: Time when the order was placed.
- `order_delivered_customer_date`: Time when the customer received the order.
- `order_estimated_delivery_date`: Promised delivery date used to measure lateness.
- `review_score`: Customer rating from 1 to 5.

## Column to KPI Mapping

### Gross Merchandise Value

- **Formula**: `SUM(price)` from order items
- **Related Columns**: `price`, `order_id`, `product_id`, `order_purchase_timestamp`
- **Why It Matters**: Measures the total value of products sold before freight and other adjustments.
- **Update Frequency**: Daily or monthly in a production pipeline.

### Total Payment Value

- **Formula**: `SUM(payment_value)` from payment records
- **Related Columns**: `payment_value`, `order_id`, `payment_type`
- **Why It Matters**: Measures the amount recorded as paid by customers.
- **Update Frequency**: Daily.
- **Caution**: An order may have multiple payment rows, so aggregate at the correct grain.

### Order Volume

- **Formula**: `COUNT(DISTINCT order_id)`
- **Related Columns**: `order_id`, `order_status`, `order_purchase_timestamp`
- **Why It Matters**: Tracks customer demand and marketplace activity.
- **Update Frequency**: Daily or weekly.

### Average Order Value

- **Formula**: `SUM(payment_value) / COUNT(DISTINCT order_id)`
- **Related Columns**: `payment_value`, `order_id`
- **Why It Matters**: Shows how much customers spend per order on average.
- **Update Frequency**: Daily or monthly.
- **Caution**: Avoid summing payment rows after joining to item rows without deduplication.

### Average Review Score

- **Formula**: `AVG(review_score)`
- **Related Columns**: `review_score`, `review_id`, `order_id`, `review_creation_date`
- **Why It Matters**: Measures customer satisfaction and service quality.
- **Update Frequency**: Weekly or monthly.

### Late Delivery Rate

- **Formula**: Delivered orders where `order_delivered_customer_date` is later than `order_estimated_delivery_date`, divided by delivered orders
- **Related Columns**: `order_status`, `order_delivered_customer_date`, `order_estimated_delivery_date`
- **Why It Matters**: Identifies fulfillment and logistics problems that can damage customer trust.
- **Update Frequency**: Weekly.

### Average Delivery Time

- **Formula**: `AVG(order_delivered_customer_date - order_purchase_timestamp)` for delivered orders
- **Related Columns**: `order_purchase_timestamp`, `order_delivered_customer_date`, `order_status`
- **Why It Matters**: Measures the end-to-end customer fulfillment experience.
- **Update Frequency**: Weekly or monthly.

### Freight Ratio

- **Formula**: `SUM(freight_value) / SUM(price)`
- **Related Columns**: `freight_value`, `price`, `order_id`, `seller_state`, `customer_state`
- **Why It Matters**: Shows how much shipping cost contributes to merchandise value.
- **Update Frequency**: Monthly.

## Ambiguous Columns & Resolutions

### Column: `customer_id`

- **Original Ambiguity**: It may appear to be the permanent identity of a shopper.
- **Resolved Meaning**: A customer record identifier associated with an order; the persistent shopper identity is `customer_unique_id`.
- **Business Interpretation**: Use it to join orders to customer address data; use `customer_unique_id` for repeat-customer analysis.
- **Proposed Rename**: `customer_record_id`
- **Risk If Misunderstood**: Unique-customer counts and lifetime-value metrics can be overstated.

### Column: `payment_value`

- **Original Ambiguity**: It may be confused with the product price or total order revenue.
- **Resolved Meaning**: Amount associated with one payment record; an order can contain multiple payment rows.
- **Business Interpretation**: Use it for payment-based customer spend, after aggregating at order grain when appropriate.
- **Proposed Rename**: `recorded_payment_amount_brl`
- **Risk If Misunderstood**: Joining payments to order items without controlling grain can double-count value.

### Column: `order_status`

- **Original Ambiguity**: It could be mistaken for payment status or delivery status only.
- **Resolved Meaning**: Overall order lifecycle status, such as delivered, canceled, shipped, or unavailable.
- **Business Interpretation**: Defines which orders should be included in completion, delivery, and cancellation KPIs.
- **Proposed Rename**: `order_lifecycle_status`
- **Risk If Misunderstood**: Fulfillment and cancellation rates may use the wrong denominator.

### Column: `product_name_lenght`

- **Original Ambiguity**: The source name contains a spelling error and may be confused with description length.
- **Resolved Meaning**: Number of characters in the product name.
- **Business Interpretation**: A product-listing completeness or merchandising attribute.
- **Proposed Rename**: `product_name_length`
- **Risk If Misunderstood**: Data-quality checks may reference a corrected name that does not exist in the raw file.

## Column Relationships

### Customer Lifetime Value

- **Definition**: `SUM(payment_value)` grouped by `customer_unique_id`, with payment rows aggregated to order grain when necessary.
- **How It Matters**: Identifies high-value and repeat customers for retention and marketing.
- **Example**: Customers with multiple completed orders can be prioritized for loyalty campaigns.
- **Related Columns**: `customer_unique_id`, `customer_id`, `order_id`, `payment_value`, `order_status`

### Revenue by Product Category

- **Definition**: `SUM(price)` grouped by `product_category_name` or its English translation.
- **How It Matters**: Shows which categories generate the most merchandise value.
- **Example**: Category performance can guide inventory, promotion, and assortment decisions.
- **Related Columns**: `product_id`, `product_category_name`, `product_category_name_english`, `price`, `order_id`

### Seller Delivery Performance

- **Definition**: Delivery duration and late-delivery rate grouped by `seller_id`.
- **How It Matters**: Identifies sellers that create fulfillment risk or poor customer experiences.
- **Example**: A seller with a high late-delivery rate may need operational intervention.
- **Related Columns**: `seller_id`, `order_id`, `shipping_limit_date`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`

### Customer Satisfaction by Seller

- **Definition**: `AVG(review_score)` grouped by `seller_id`.
- **How It Matters**: Detects sellers with consistently poor customer feedback.
- **Example**: Low scores combined with late deliveries indicate a seller trust-and-safety risk.
- **Related Columns**: `seller_id`, `order_id`, `review_id`, `review_score`

