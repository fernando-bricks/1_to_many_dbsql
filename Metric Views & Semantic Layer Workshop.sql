-- Databricks notebook source
-- DBTITLE 1,Workshop Introduction
-- MAGIC %md
-- MAGIC # Metric Views & Semantic Layer Workshop
-- MAGIC
-- MAGIC ## What are Metric Views?
-- MAGIC
-- MAGIC Metric Views are Unity Catalog objects that centralize business metric definitions in a **Semantic Layer**. Unlike standard views that lock in aggregations at creation time, metric views separate:
-- MAGIC
-- MAGIC * **Measures** (aggregate calculations like SUM, COUNT, AVG)
-- MAGIC * **Dimensions** (categorical attributes for grouping)
-- MAGIC
-- MAGIC This separation enables flexible analysis at query time while ensuring consistent metric definitions across all downstream assets (dashboards, notebooks, Genie spaces).
-- MAGIC
-- MAGIC ## Key Benefits
-- MAGIC
-- MAGIC ✅ **Consistency**: Define metrics once, use everywhere  
-- MAGIC ✅ **Flexibility**: Query any combination of dimensions and measures  
-- MAGIC ✅ **Governance**: Centralized metric definitions with Unity Catalog permissions  
-- MAGIC ✅ **Performance**: Optional materialization for faster queries  
-- MAGIC ✅ **AI-Ready**: Semantic metadata (synonyms, display names) for Genie and AI tools
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC ## Workshop Dataset: Coffee Shop Analytics
-- MAGIC
-- MAGIC In this workshop, we'll explore the `catalog.schema.coffee_metric_view` which tracks:
-- MAGIC
-- MAGIC * **Transactions** from multiple coffee shop stores
-- MAGIC * **Products** sold (with details)
-- MAGIC * **Store information** and reviews
-- MAGIC * **Time dimensions** (date, hour of day)
-- MAGIC
-- MAGIC ### Metric View Structure
-- MAGIC
-- MAGIC **Dimensions:**
-- MAGIC * `product` - Product ID
-- MAGIC * `Product detail` - Product description
-- MAGIC * `store_name` - Store name
-- MAGIC * `month_day` - Transaction date
-- MAGIC * `hour_of_day` - Hour when transaction occurred
-- MAGIC
-- MAGIC **Measures:**
-- MAGIC * `total_transactions` - Count of transactions
-- MAGIC * `total_sales` - Total revenue
-- MAGIC * `total_quantity_sold` - Total items sold

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Section 1: Basic Querying Syntax
-- MAGIC
-- MAGIC ### Critical Rules for Querying Metric Views
-- MAGIC
-- MAGIC 1. **Wrap measures with MEASURE()** - `MEASURE(\`total_sales\`)`
-- MAGIC 2. **Always use GROUP BY ALL** - Required for all queries
-- MAGIC 3. **Never use SELECT \*** - Explicitly list dimensions and measures
-- MAGIC 4. **Backtick all names** - Especially names with spaces
-- MAGIC 5. **No nested aggregations** - MIN/MAX/AVG on measures not allowed
-- MAGIC
-- MAGIC Let's start with simple queries and build up complexity!

-- COMMAND ----------

USE CATALOG dbacademy; -- Need to be updated 
Use SCHEMA <insert_your_schema>; -- Need to be updated

-- COMMAND ----------

-- DBTITLE 1,Query 1: Sales by Store
-- Basic aggregation: Sales performance by store
-- This demonstrates grouping by a dimension and selecting multiple measures
SELECT 
  `store_name`,
  MEASURE(`total_sales`) AS revenue,
  MEASURE(`total_transactions`) AS transactions,
  MEASURE(`total_quantity_sold`) AS items_sold
FROM coffee_metric_view
GROUP BY ALL
ORDER BY revenue DESC

-- COMMAND ----------

-- DBTITLE 1,Query 2: Product Performance
-- Multiple dimensions: Product performance with details
SELECT 
  `product`,
  `Product detail`,
  MEASURE(`total_sales`) AS revenue,
  MEASURE(`total_quantity_sold`) AS quantity
FROM coffee_metric_view
GROUP BY ALL
ORDER BY revenue DESC
LIMIT 10

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Section 2: Time-Based Analysis
-- MAGIC
-- MAGIC Metric views excel at time-series analysis. Let's explore sales patterns over time and by hour of day.

-- COMMAND ----------

-- DBTITLE 1,Query 3: Sales by Hour of Day
-- Time-based analysis: Peak hours analysis
-- Shows when customers buy the most throughout the day
SELECT 
  `hour_of_day`,
  MEASURE(`total_sales`) AS revenue,
  MEASURE(`total_transactions`) AS transactions,
  ROUND(MEASURE(`total_sales`) / MEASURE(`total_transactions`), 2) AS avg_transaction_value
FROM coffee_metric_view
GROUP BY ALL
ORDER BY `hour_of_day`

-- COMMAND ----------

-- DBTITLE 1,Section 3: Advanced Patterns
-- MAGIC %md
-- MAGIC ## Section 3: Advanced Query Patterns
-- MAGIC
-- MAGIC Let's explore sophisticated analytical patterns:
-- MAGIC
-- MAGIC * **Calculated metrics** combining multiple measures
-- MAGIC * **Top-K queries** using window functions for ranking

-- COMMAND ----------

-- DBTITLE 1,Query 4: Calculated Metrics
-- Calculate average transaction value and price per item
SELECT 
  `store_name`,
  MEASURE(`total_sales`) AS total_revenue,
  MEASURE(`total_transactions`) AS transactions,
  MEASURE(`total_quantity_sold`) AS items_sold,
  ROUND(MEASURE(`total_sales`) / MEASURE(`total_transactions`), 2) AS avg_transaction_value,
  ROUND(MEASURE(`total_sales`) / MEASURE(`total_quantity_sold`), 2) AS avg_price_per_item
FROM coffee_metric_view
GROUP BY ALL
ORDER BY total_revenue DESC

-- COMMAND ----------

-- DBTITLE 1,Query 5: Top Products (ROW_NUMBER)
-- Top-K query: Best selling products using ROW_NUMBER()
WITH ranked_products AS (
  SELECT 
    `Product detail`,
    MEASURE(`total_sales`) AS revenue,
    MEASURE(`total_quantity_sold`) AS quantity,
    ROW_NUMBER() OVER (ORDER BY MEASURE(`total_sales`) DESC) AS rank
  FROM coffee_metric_view
  GROUP BY ALL
)
SELECT 
  rank,
  `Product detail`,
  revenue,
  quantity
FROM ranked_products
WHERE rank <= 5

-- COMMAND ----------

-- DBTITLE 1,Section 4: Creating Metric Views
-- MAGIC %md
-- MAGIC ## Section 4: Creating Metric Views
-- MAGIC
-- MAGIC ### YAML Structure
-- MAGIC
-- MAGIC Metric views are defined using SQL DDL with YAML:
-- MAGIC
-- MAGIC ```sql
-- MAGIC CREATE OR REPLACE VIEW catalog.schema.metric_view_name
-- MAGIC WITH METRICS
-- MAGIC LANGUAGE YAML
-- MAGIC AS $$
-- MAGIC   version: 1.1
-- MAGIC   source: catalog.schema.source_table
-- MAGIC   dimensions:
-- MAGIC     - name: dimension_name
-- MAGIC       expr: column_or_expression
-- MAGIC       display_name: Human Readable Name  # Optional
-- MAGIC   measures:
-- MAGIC     - name: measure_name
-- MAGIC       expr: aggregate_expression
-- MAGIC       format:                            # Optional
-- MAGIC         type: currency
-- MAGIC         currency_code: USD
-- MAGIC $$
-- MAGIC ```
-- MAGIC
-- MAGIC **Key Fields:**
-- MAGIC * `version: 1.1` - Latest version
-- MAGIC * `source` - Base table or SQL query
-- MAGIC * `dimensions` - Categorical attributes
-- MAGIC * `measures` - Aggregate calculations
-- MAGIC * `joins` - Star/snowflake schema (optional)
-- MAGIC * `display_name`, `comment`, `synonyms` - Semantic metadata (optional)

-- COMMAND ----------

-- DBTITLE 1,Our Coffee Metric View
-- MAGIC %md
-- MAGIC ### Our Coffee Shop Metric View
-- MAGIC
-- MAGIC The `users.tayyab_ali.coffee_metric_view` demonstrates:
-- MAGIC
-- MAGIC **Star Schema with Joins:**
-- MAGIC * Fact table: `fct_coffee_shop_transactions`
-- MAGIC * Dimension tables: `dim_coffee_shop_stores`, `dim_coffee_products`
-- MAGIC * Nested join: Store reviews (snowflake pattern)
-- MAGIC
-- MAGIC **Dimensions:**
-- MAGIC * `product`, `Product detail` - Product information
-- MAGIC * `store_name` - Store name from dimension table
-- MAGIC * `month_day` - Derived from `transaction_date`
-- MAGIC * `hour_of_day` - Extracted from `transaction_time`
-- MAGIC
-- MAGIC **Measures:**
-- MAGIC * `total_transactions` - SUM(transaction_id)
-- MAGIC * `total_sales` - ROUND(sum(transation_total), 2)
-- MAGIC * `total_quantity_sold` - SUM(transaction_qty)

-- COMMAND ----------

-- DBTITLE 1,Section 5: Best Practices
-- MAGIC %md
-- MAGIC ## Section 5: Semantic Layer & Best Practices
-- MAGIC
-- MAGIC ### What is a Semantic Layer?
-- MAGIC
-- MAGIC A **Semantic Layer** translates technical schemas into business terminology, providing:
-- MAGIC * Consistent metric definitions across the organization
-- MAGIC * Self-service analytics for non-technical users
-- MAGIC * AI-ready metadata for tools like Genie
-- MAGIC
-- MAGIC ### Semantic Metadata
-- MAGIC
-- MAGIC Enhance metric views with:
-- MAGIC
-- MAGIC **Display Names & Comments:**
-- MAGIC ```yaml
-- MAGIC measures:
-- MAGIC   - name: total_sales
-- MAGIC     expr: SUM(amount)
-- MAGIC     display_name: Total Revenue
-- MAGIC     comment: Sum of all transaction amounts in USD
-- MAGIC ```
-- MAGIC
-- MAGIC **Formatting:**
-- MAGIC ```yaml
-- MAGIC format:
-- MAGIC   type: currency
-- MAGIC   currency_code: USD
-- MAGIC   decimal_places:
-- MAGIC     type: exact
-- MAGIC     places: 2
-- MAGIC ```
-- MAGIC
-- MAGIC **Synonyms** (for AI/Genie):
-- MAGIC ```yaml
-- MAGIC synonyms:
-- MAGIC   - revenue
-- MAGIC   - sales
-- MAGIC ```
-- MAGIC
-- MAGIC ### Best Practices
-- MAGIC
-- MAGIC 1. **Use clear, business-friendly names** - Avoid technical jargon
-- MAGIC 2. **Document everything** - Add comments to dimensions and measures
-- MAGIC 3. **Compose metrics** - Reference other measures using MEASURE()
-- MAGIC 4. **Use materialization** - Pre-compute for expensive queries
-- MAGIC 5. **Control access** - Use Unity Catalog permissions
-- MAGIC 6. **Integrate everywhere** - Use in Lakeview Dashboards, Genie, SQL, Python

-- COMMAND ----------

-- DBTITLE 1,Section 6: Hands-On Exercises
-- MAGIC %md
-- MAGIC ## Section 6: Hands-On Exercises
-- MAGIC
-- MAGIC Try these exercises to practice querying metric views:
-- MAGIC
-- MAGIC ### Exercise 1: Peak Hours Analysis
-- MAGIC **Goal**: Find which hour of the day has the highest average transaction value
-- MAGIC
-- MAGIC **Hint**: Calculate `total_sales / total_transactions` grouped by `hour_of_day`
-- MAGIC
-- MAGIC ### Exercise 2: Product Performance Matrix
-- MAGIC **Goal**: Create a report showing each product's revenue, quantity sold, and average price
-- MAGIC
-- MAGIC **Hint**: Use all three measures and calculate `total_sales / total_quantity_sold`
-- MAGIC
-- MAGIC ---
-- MAGIC
-- MAGIC **Try writing these queries in the cells below!**

-- COMMAND ----------

-- DBTITLE 1,Exercise 1: Your Solution
-- Exercise 1: Peak Hours Analysis
-- Write your query here



-- COMMAND ----------

-- DBTITLE 1,Exercise 2: Your Solution
-- Exercise 2: Product Performance Matrix
-- Write your query here



-- COMMAND ----------

-- DBTITLE 1,Workshop Summary
-- MAGIC %md
-- MAGIC ## Workshop Summary
-- MAGIC
-- MAGIC ### Key Takeaways
-- MAGIC
-- MAGIC ✅ **Metric Views** separate measures from dimensions for flexible analysis  
-- MAGIC ✅ **Query Syntax**: MEASURE() wrapper, GROUP BY ALL, backticks required  
-- MAGIC ✅ **Advanced Patterns**: Calculated metrics, Top-K with ROW_NUMBER()  
-- MAGIC ✅ **YAML Definition**: version, source, dimensions, measures, joins  
-- MAGIC ✅ **Semantic Layer**: Business-friendly metadata powers Genie and dashboards
-- MAGIC
-- MAGIC ### Next Steps
-- MAGIC
-- MAGIC 1. Run the queries in this notebook
-- MAGIC 2. Create metric views for your datasets
-- MAGIC 3. Build Lakeview dashboards
-- MAGIC 4. Try Genie with natural language queries
-- MAGIC 5. Add materialization for performance
-- MAGIC
-- MAGIC ### Resources
-- MAGIC
-- MAGIC * [Metric Views Documentation](https://docs.databricks.com/en/sql/language-manual/sql-ref-metric-views.html)
-- MAGIC * [Unity Catalog Best Practices](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)
-- MAGIC * [Genie Spaces](https://docs.databricks.com/en/genie/index.html)
-- MAGIC
-- MAGIC **Happy Analyzing! ☕️📊**

-- COMMAND ----------

-- DBTITLE 1,Solution 1: Peak Hours Analysis
-- Solution 1: Peak Hours Analysis
SELECT 
  `hour_of_day`,
  MEASURE(`total_sales`) AS total_revenue,
  MEASURE(`total_transactions`) AS transactions,
  ROUND(MEASURE(`total_sales`) / MEASURE(`total_transactions`), 2) AS avg_transaction_value
FROM coffee_metric_view
GROUP BY ALL
ORDER BY avg_transaction_value DESC

-- COMMAND ----------

-- DBTITLE 1,Solution 2: Product Performance Matrix
-- Solution 2: Product Performance Matrix
SELECT 
  `Product detail`,
  MEASURE(`total_sales`) AS revenue,
  MEASURE(`total_quantity_sold`) AS quantity_sold,
  ROUND(MEASURE(`total_sales`) / MEASURE(`total_quantity_sold`), 2) AS avg_price_per_item
FROM coffee_metric_view
GROUP BY ALL
ORDER BY revenue DESC