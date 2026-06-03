# Databricks notebook source
# DBTITLE 1,Create Coffee Metric View
# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW users.fernando_vasquez.coffee_metric_view
# MAGIC WITH METRICS
# MAGIC LANGUAGE YAML
# MAGIC AS $$
# MAGIC version: 1.2
# MAGIC
# MAGIC source: users.fernando_vasquez.fct_coffee_shop_transactions
# MAGIC
# MAGIC joins:
# MAGIC   - name: dim_coffee_shop_stores
# MAGIC     source: users.fernando_vasquez.dim_coffee_shop_stores
# MAGIC     "on": source.store_id = dim_coffee_shop_stores.store_id
# MAGIC     joins:
# MAGIC       - name: fct_coffee_shop_stores_reviews
# MAGIC         source: users.fernando_vasquez.fct_coffee_shop_stores_reviews
# MAGIC         "on": dim_coffee_shop_stores.store_id = fct_coffee_shop_stores_reviews.store_id
# MAGIC   - name: dim_coffee_products
# MAGIC     source: users.fernando_vasquez.dim_coffee_products
# MAGIC     "on": source.product_iD = dim_coffee_products.product_id
# MAGIC
# MAGIC dimensions:
# MAGIC   - name: product
# MAGIC     expr: source.product_iD
# MAGIC     comment: Unique identifier for the coffee product
# MAGIC     display_name: Product ID
# MAGIC   - name: Product detail
# MAGIC     expr: dim_coffee_products.product_detail
# MAGIC     comment: Full descriptive name and details of the coffee product
# MAGIC     display_name: Product Detail
# MAGIC   - name: store_name
# MAGIC     expr: dim_coffee_shop_stores.store_name
# MAGIC     comment: Name of the coffee shop store where the transaction occurred
# MAGIC     display_name: Store Name
# MAGIC   - name: month_day
# MAGIC     expr: "make_date(year(transaction_date), month(transaction_date), day(transaction_date))"
# MAGIC     comment: Date of the transaction derived from the transaction timestamp
# MAGIC     display_name: Transaction Date
# MAGIC   - name: hour_of_day
# MAGIC     expr: HOUR(transaction_time)
# MAGIC     comment: Hour of the day (0-23) when the transaction took place
# MAGIC     display_name: Hour of Day
# MAGIC
# MAGIC measures:
# MAGIC   - name: total_transactions
# MAGIC     expr: SUM(transaction_id)
# MAGIC     comment: Sum of all transaction IDs, representing overall transaction volume
# MAGIC     display_name: Total Transactions
# MAGIC   - name: total_sales
# MAGIC     expr: "ROUND(sum(transation_total),2)"
# MAGIC     comment: Total revenue from all transactions, rounded to two decimal places
# MAGIC     display_name: Total Sales
# MAGIC     format:
# MAGIC       type: currency
# MAGIC       currency_code: USD
# MAGIC       decimal_places:
# MAGIC         type: exact
# MAGIC         places: 2
# MAGIC   - name: total_quantity_sold
# MAGIC     expr: SUM(transaction_qty)
# MAGIC     comment: Total number of items sold across all transactions
# MAGIC     display_name: Total Quantity Sold
# MAGIC $$;