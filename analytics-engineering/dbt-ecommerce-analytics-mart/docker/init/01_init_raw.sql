-- Loads the real Olist CSVs (mounted read-only at /seeds_raw) into a `raw` schema
-- via COPY. dbt sources point at these tables. We use COPY instead of `dbt seed`
-- because dbt seed inserts row-by-row via generated INSERT statements, which does
-- not scale to Olist's ~100k-row fact tables; COPY is the correct tool for bulk
-- loading raw extracts, while dbt seed stays reserved for small static lookups.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.olist_customers (
    customer_id varchar(64) PRIMARY KEY,
    customer_unique_id varchar(64) NOT NULL,
    customer_zip_code_prefix varchar(10),
    customer_city varchar(128),
    customer_state varchar(2)
);

CREATE TABLE raw.olist_orders (
    order_id varchar(64) PRIMARY KEY,
    customer_id varchar(64) NOT NULL,
    order_status varchar(32),
    order_purchase_timestamp timestamp,
    order_approved_at timestamp,
    order_delivered_carrier_date timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date timestamp
);

CREATE TABLE raw.olist_order_items (
    order_id varchar(64) NOT NULL,
    order_item_id int NOT NULL,
    product_id varchar(64) NOT NULL,
    seller_id varchar(64) NOT NULL,
    shipping_limit_date timestamp,
    price numeric(12, 2),
    freight_value numeric(12, 2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE raw.olist_order_payments (
    order_id varchar(64) NOT NULL,
    payment_sequential int NOT NULL,
    payment_type varchar(32),
    payment_installments int,
    payment_value numeric(12, 2),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE raw.olist_products (
    product_id varchar(64) PRIMARY KEY,
    product_category_name varchar(128),
    product_name_lenght int,
    product_description_lenght int,
    product_photos_qty int,
    product_weight_g numeric,
    product_length_cm numeric,
    product_height_cm numeric,
    product_width_cm numeric
);

CREATE TABLE raw.product_category_name_translation (
    product_category_name varchar(128) PRIMARY KEY,
    product_category_name_english varchar(128)
);

\copy raw.olist_customers FROM '/seeds_raw/olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
\copy raw.olist_orders FROM '/seeds_raw/olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
\copy raw.olist_order_items FROM '/seeds_raw/olist_order_items_dataset.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
\copy raw.olist_order_payments FROM '/seeds_raw/olist_order_payments_dataset.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
\copy raw.olist_products FROM '/seeds_raw/olist_products_dataset.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
\copy raw.product_category_name_translation FROM '/seeds_raw/product_category_name_translation.csv' WITH (FORMAT csv, HEADER true, QUOTE '"');
