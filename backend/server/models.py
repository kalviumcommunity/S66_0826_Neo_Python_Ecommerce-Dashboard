"""SQLAlchemy ORM models for the E-commerce Analytics database."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, Float, String, Text
from server.database import Base


class Order(Base):
    """Order metadata and timeline."""

    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    order_status = Column(String, index=True)
    order_purchase_timestamp = Column(String, index=True)
    order_approved_at = Column(String, nullable=True)
    order_delivered_carrier_date = Column(String, nullable=True)
    order_delivered_customer_date = Column(String, nullable=True)
    order_estimated_delivery_date = Column(String, nullable=True)


class OrderItem(Base):
    """Line items for customer orders."""

    __tablename__ = "order_items"

    order_id = Column(String, primary_key=True)
    order_item_id = Column(BigInteger, primary_key=True)
    product_id = Column(String, index=True)
    seller_id = Column(String, index=True)
    shipping_limit_date = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    freight_value = Column(Float, default=0.0)


class OrderPayment(Base):
    """Payment methods and transaction values."""

    __tablename__ = "order_payments"

    order_id = Column(String, primary_key=True)
    payment_sequential = Column(BigInteger, primary_key=True)
    payment_type = Column(String)
    payment_installments = Column(BigInteger, default=1)
    payment_value = Column(Float, default=0.0)


class Customer(Base):
    """Customer demographic and location records."""

    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    customer_unique_id = Column(String, index=True)
    customer_zip_code_prefix = Column(BigInteger)
    customer_city = Column(String)
    customer_state = Column(String, index=True)


class Seller(Base):
    """Merchant identity and location records."""

    __tablename__ = "sellers"

    seller_id = Column(String, primary_key=True, index=True)
    seller_zip_code_prefix = Column(BigInteger, nullable=True)
    seller_city = Column(String, nullable=True)
    seller_state = Column(String, nullable=True)


class OrderReview(Base):
    """Customer satisfaction ratings and feedback."""

    __tablename__ = "order_reviews"

    review_id = Column(String, primary_key=True)
    order_id = Column(String, primary_key=True, index=True)
    review_score = Column(BigInteger, index=True)
    review_comment_title = Column(Text, nullable=True)
    review_comment_message = Column(Text, nullable=True)
    review_creation_date = Column(String, nullable=True)
    review_answer_timestamp = Column(String, nullable=True)


class Product(Base):
    """Catalog product attributes and categories."""

    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    product_category_name = Column(String, index=True)
    product_name_lenght = Column(Float, nullable=True)
    product_description_lenght = Column(Float, nullable=True)
    product_photos_qty = Column(Float, nullable=True)
    product_weight_g = Column(Float, nullable=True)
    product_length_cm = Column(Float, nullable=True)
    product_height_cm = Column(Float, nullable=True)
    product_width_cm = Column(Float, nullable=True)


class ProductCategoryNameTranslation(Base):
    """Translation table from Portuguese category names to English."""

    __tablename__ = "product_category_name_translation"

    product_category_name = Column(String, primary_key=True)
    product_category_name_english = Column(String, nullable=True)


class AggSellerPerformance(Base):
    """Pre-computed seller performance rollups."""

    __tablename__ = "agg_seller_performance"

    seller_id = Column(String, primary_key=True, index=True)
    seller_state = Column(String, nullable=True)
    seller_city = Column(String, nullable=True)
    total_orders = Column(BigInteger, default=0)
    total_items_sold = Column(BigInteger, default=0)
    total_merchandise_value = Column(Float, default=0.0)
    total_freight_value = Column(Float, default=0.0)
    late_deliveries_count = Column(BigInteger, default=0)
    avg_review_score = Column(Float, default=0.0)
    updated_at = Column(String, nullable=True)
