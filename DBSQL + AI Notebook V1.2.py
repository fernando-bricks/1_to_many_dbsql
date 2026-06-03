# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # DBSQL + AI Workshop: "Mining Insights from the gold layer"
# MAGIC This hands-on workshop is designed to empower data analysts, engineers, and business users to extract maximum value from their refined, business-ready datasets using Databricks' unified analytics platform. The "Gold Layer" refers to the curated, high-quality data tier in the medallion architecture that's optimized for analytics and reporting.
# MAGIC
# MAGIC <div style="display: flex; align-items: center;">
# MAGIC   <img src="Images/Data + AI.png" alt="generated-image.png" style="margin-left: 10px;" width="250"/>
# MAGIC   <ul>
# MAGIC     <li>Unity Catalog managed tables: advantages and advanced uses</li>
# MAGIC     <li>Leverage AI SQL functions to enrich data and extract insights</li>
# MAGIC     <li>Correctly develop AI/BI Dashboards, use AI to facilitate your visualizations</li>
# MAGIC     <li>Set up a genie space to empower your business users with last-mile analytics</li>
# MAGIC     <li>Finally, combine Dashboards and Genie to get the full AI/BI experience</li>
# MAGIC   </ul>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,Run setup script
# MAGIC %run
# MAGIC ./Scripts/script_0

# COMMAND ----------

# DBTITLE 1,Set up a definition for the Catalog and Schema
# MAGIC %sql
# MAGIC USE CATALOG users; -- Need to be updated 
# MAGIC Use SCHEMA fernando_vasquez; -- Need to be updated

# COMMAND ----------

# MAGIC %md
# MAGIC ## Good Coffee CO
# MAGIC Let's develop a comprehensive insights strategy for the board of directors, enabling them to make informed decisions regarding the current and future success of the most promising coffee chain since Starbucks!

# COMMAND ----------

# DBTITLE 1,First glance at the dataset
# MAGIC %sql
# MAGIC SELECT * FROM fct_coffee_shop_transactions LIMIT 20
# MAGIC --SELECT * FROM fct_coffee_shop_stores_reviews LIMIT 10
# MAGIC --SELECT * FROM dim_coffee_shop_stores LIMIT 10
# MAGIC --SELECT * FROM dim_coffee_products  LIMIT 10

# COMMAND ----------

# DBTITLE 1,Agg_1: Transactions, sales and quantity sold by store, product and month for 2023
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   store_name,
# MAGIC   product_detail,
# MAGIC   make_date(year(transaction_date), month(transaction_date), day(transaction_date)) AS month_day,
# MAGIC   SUM(transaction_id) AS total_transactions,
# MAGIC   ROUND(sum(transation_total),2) AS total_sales,
# MAGIC   SUM(transaction_qty) AS total_quantity_sold
# MAGIC FROM 
# MAGIC   fct_coffee_shop_transactions
# MAGIC LEFT JOIN dim_coffee_shop_stores 
# MAGIC   ON fct_coffee_shop_transactions.store_id = dim_coffee_shop_stores.store_id
# MAGIC LEFT JOIN dim_coffee_products 
# MAGIC   ON fct_coffee_shop_transactions.product_id = dim_coffee_products.product_id
# MAGIC WHERE
# MAGIC   YEAR(transaction_date) = 2023
# MAGIC GROUP BY 
# MAGIC   store_name,
# MAGIC   product_detail,
# MAGIC   month_day
# MAGIC ORDER BY 
# MAGIC   store_name,
# MAGIC   month_day
# MAGIC
# MAGIC

# COMMAND ----------

# DBTITLE 1,Top 10 products by total quantity sold
# MAGIC %sql
# MAGIC SELECT
# MAGIC   product_detail,
# MAGIC   SUM(transaction_qty) AS total_quantity_sold
# MAGIC FROM
# MAGIC   fct_coffee_shop_transactions AS transactions
# MAGIC LEFT JOIN dim_coffee_products AS products 
# MAGIC   ON transactions.product_id = products.product_id
# MAGIC GROUP BY
# MAGIC   product_detail
# MAGIC ORDER BY
# MAGIC  total_quantity_sold DESC
# MAGIC  limit 10;

# COMMAND ----------

# DBTITLE 1,Agg_3: Transactions and total sales per hour
# MAGIC %sql
# MAGIC SELECT
# MAGIC   store_name,
# MAGIC   HOUR(transaction_time) AS hour_of_day,
# MAGIC   SUM(transaction_qty) AS total_transactions_per_hour,
# MAGIC   ROUND(SUM(transation_total),2) AS total_store_sales_per_hour
# MAGIC FROM
# MAGIC   fct_coffee_shop_transactions AS transactions
# MAGIC LEFT JOIN dim_coffee_shop_stores AS stores
# MAGIC   ON transactions.store_id = stores.store_id 
# MAGIC GROUP BY
# MAGIC   HOUR(transaction_time), store_name
# MAGIC ORDER BY
# MAGIC  store_name, hour_of_day ASC
# MAGIC

# COMMAND ----------

# DBTITLE 1,Agg_4: Total review by store
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   store_name,
# MAGIC   COUNT(review_id) AS total_reviews
# MAGIC FROM 
# MAGIC   fct_coffee_shop_stores_reviews AS reviews
# MAGIC LEFT JOIN dim_coffee_shop_stores AS stores
# MAGIC   ON reviews.store_id = stores.store_id
# MAGIC GROUP BY 
# MAGIC   store_name
# MAGIC ORDER BY 
# MAGIC   total_reviews DESC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Batch Inference: "SQL AI functions"
# MAGIC Let's leverage Batch Inference to give a more personalized description and to review the current data by analyzing the sentiment of the reviews
# MAGIC
# MAGIC <div style="display: flex; align-items: center;">
# MAGIC   <img src="Images/Coffee and AI.png" alt="generated-image.png" style="margin-left: 10px;" width="300"/>
# MAGIC </div>
# MAGIC

# COMMAND ----------

# DBTITLE 1,This code creates a more flexible description of each product
# MAGIC %sql
# MAGIC --CREATE OR REPLACE TABLE users.fernando_vasquez.dim_coffee_products_extended AS (
# MAGIC WITH distict_products AS (
# MAGIC   SELECT DISTINCT 
# MAGIC   product_id,
# MAGIC   product_category,
# MAGIC   product_detail,
# MAGIC   unit_price
# MAGIC FROM dim_coffee_products 
# MAGIC )
# MAGIC SELECT product_id,product_category,product_detail,
# MAGIC       ai_query('databricks-meta-llama-3-3-70b-instruct',
# MAGIC     CONCAT(
# MAGIC       "Create a description of the product based on the product category",product_category,"and detail",product_detail,"and unit price in dollars",unit_price,"The output should be just the description and vary for each product")) AS PRODUCT_DESCRIPTION
# MAGIC  FROM distict_products 
# MAGIC  ORDER BY product_id DESC
# MAGIC  LIMIT 35
# MAGIC --)

# COMMAND ----------

# DBTITLE 1,Create the fact table for reviewing the sentiment
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE fct_coffee_shop_stores_reviews_sentiment AS (
# MAGIC   SELECT 
# MAGIC     review_id,
# MAGIC     store_id,
# MAGIC     email,
# MAGIC     review,
# MAGIC     score, 
# MAGIC     ai_analyze_sentiment(review) AS sentiment
# MAGIC   FROM 
# MAGIC     fct_coffee_shop_stores_reviews
# MAGIC ) 

# COMMAND ----------

# DBTITLE 1,Agg_5: Total Review by Sentiment
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   sentiment,
# MAGIC   count(review_id) AS total_reviews
# MAGIC FROM 
# MAGIC   fct_coffee_shop_stores_reviews_sentiment
# MAGIC GROUP BY 
# MAGIC   sentiment

# COMMAND ----------

# DBTITLE 1,Create a email with discounts to mixed sentiment
# MAGIC %sql
# MAGIC WITH reviews_combined  AS (
# MAGIC SELECT 
# MAGIC   fct_reviews.review_id,
# MAGIC   review,
# MAGIC   email,
# MAGIC   sentiment,
# MAGIC   store_name
# MAGIC FROM 
# MAGIC   fct_coffee_shop_stores_reviews_sentiment AS fct_reviews 
# MAGIC LEFT JOIN dim_coffee_shop_stores AS dim_stores ON fct_reviews.store_id = dim_stores.store_id 
# MAGIC )
# MAGIC
# MAGIC SELECT 
# MAGIC   review_id, 
# MAGIC   email,
# MAGIC       ai_gen(concat("Use this review:",review,"to create a email advertising a 10% discount at the store:",store_name,"Use the email:", email, "as to infer the user name",". The output should be just the email and vary for each review")) AS advertising_emails
# MAGIC FROM 
# MAGIC   reviews_combined
# MAGIC WHERE 
# MAGIC   sentiment = "mixed" limit 15

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Dashboard: "Tables to visualizations"
# MAGIC Now that we understand the data, and move the insights to production!
# MAGIC
# MAGIC <div style="display: flex; align-items: right;">
# MAGIC   <img src="Images/Coffee Sales.png" alt="Coffee Sales" style="margin-left: 10px;" width="300"/>
# MAGIC </div>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Genie: "powerful text to insights assistant"
# MAGIC Convert your business questions and last-mile analytics to SQL easily with Genie!
# MAGIC
# MAGIC
# MAGIC <div style="display: flex; align-items: right;">
# MAGIC  <img src="Images/Genie.png" alt="Genie" style="margin-left: 10px;" width="400"/>
# MAGIC </div>
# MAGIC
# MAGIC ### Here we will consider best practices when setting up the genie space:
# MAGIC
# MAGIC * **Focused Datasets:** Genie should be product/project focus.
# MAGIC * **Leverage UC metadata:** Give proper table and column descriptions.
# MAGIC * **Give Genie SQL examples:** Add a natural language question that reflects what a business user would ask.
# MAGIC * **Add Joins:** Explain to gneie the relationship of your data.
# MAGIC * **Add instructions:** Help Genie understand the business context on meanings, formatting, and business rules.
# MAGIC
# MAGIC
# MAGIC In this workshop, we covered the first 2 Best practices at the beginning when we covered the UC tables.
# MAGIC
# MAGIC ### Lets create a Genie Space to work as a  Coffee Information Asistant 
# MAGIC
# MAGIC #### **Description:** 
# MAGIC This assistant will use data about the transactions, reviews, and sales of coffee stores. Additionally, it includes information about the different products available in the chain.
# MAGIC
# MAGIC #### **Guide the users:** 
# MAGIC
# MAGIC For example, SQL, let's review a couple of questions
# MAGIC
# MAGIC #### **Instructions:** 
# MAGIC
# MAGIC * Adress to the user in the most formal way 
# MAGIC * Any product with total sales bellow 800 is at risk of beeing removed from the Menu
# MAGIC * Stores should consider negative very seriusly 
# MAGIC * Hours with less than 10000 total sells could be removed 
# MAGIC * Customer satisfaction its very important for corportate
# MAGIC * Better customer experience is more important than total sells
# MAGIC * All the data related to money (Like sales or price) should be assumed as in dollars 
# MAGIC * The best product is the one with the highest sales
# MAGIC
# MAGIC #### **Sample questions:** 
# MAGIC * What is the best time selling time for the chain?
# MAGIC * How much reviews have a negative and whats their average score?
# MAGIC * What products should we remove?
# MAGIC
# MAGIC
# MAGIC
# MAGIC #### **Joins:** 
# MAGIC Define the 3 joins shown on this Entity Relatioship Diagram 
# MAGIC
# MAGIC
# MAGIC <div style="display: flex; align-items: right;">
# MAGIC  <img src="Images/Coffee EDR.png" alt="Genie" style="margin-left: 10px;" width="600"/>
# MAGIC </div>
# MAGIC
# MAGIC
# MAGIC #### **Example, SQL:** 
# MAGIC

# COMMAND ----------

# DBTITLE 1,SQL Example 1
# MAGIC %sql
# MAGIC --What is the top 3 best selling product for the store Astoria Brews store?
# MAGIC --This is relevant because it helps us understand what products are popular with customers and for marketing strategies.
# MAGIC SELECT
# MAGIC   store_name,
# MAGIC   product_detail,
# MAGIC   SUM(transation_total) AS total_quantity_sold
# MAGIC FROM
# MAGIC   fct_coffee_shop_transactions AS transactions
# MAGIC LEFT JOIN dim_coffee_products AS products 
# MAGIC   ON transactions.product_id = products.product_id
# MAGIC LEFT JOIN dim_coffee_shop_stores AS stores
# MAGIC   ON transactions.store_id = stores.store_id
# MAGIC WHERE
# MAGIC   store_name = 'Astoria Brews'
# MAGIC GROUP BY
# MAGIC   store_name,
# MAGIC   product_detail
# MAGIC ORDER BY
# MAGIC   total_quantity_sold DESC
# MAGIC LIMIT 3
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC --What's the most crowded time for Lower Grounds Coffee Co?  
# MAGIC --This is relevant because it helps us understand when the store is most busy and can help us plan for staffing
# MAGIC SELECT
# MAGIC   store_name,
# MAGIC   HOUR(transaction_time) AS hour_of_day,
# MAGIC   ROUND(SUM(transation_total),2) AS total_transactions
# MAGIC FROM
# MAGIC   fct_coffee_shop_transactions AS transactions
# MAGIC LEFT JOIN dim_coffee_shop_stores AS stores
# MAGIC   ON transactions.store_id = stores.store_id
# MAGIC WHERE
# MAGIC   store_name = 'Lower Grounds Coffee Co'
# MAGIC GROUP BY  store_name, hour_of_day
# MAGIC
# MAGIC ORDER BY
# MAGIC   total_transactions DESC
# MAGIC LIMIT 1

# COMMAND ----------

# DBTITLE 1,Setting Up Your Genie Space
# MAGIC %md
# MAGIC ---
# MAGIC ### Setting Up Your Genie Space
# MAGIC
# MAGIC A Genie Space works best when it has rich context beyond just tables and columns. In this section you will configure your Genie Space by adding a **description**, **general instructions**, **sample questions**, **table joins**, and **trusted assets (SQL examples)**.
# MAGIC
# MAGIC Refer to the best practices and configuration details in the section above, then follow each exercise below step by step.

# COMMAND ----------

# DBTITLE 1,Exercise — Create the Genie Space
# MAGIC %md
# MAGIC ### Exercise — Create the Genie Space & Add Tables
# MAGIC
# MAGIC 1. In the Databricks sidebar, click **+ New** > **Genie space**
# MAGIC 2. Name it: **Good Coffee Co — Information Assistant**
# MAGIC 3. Add the following **description:**
# MAGIC
# MAGIC ```
# MAGIC This assistant uses data about the transactions, reviews, and sales of coffee stores.
# MAGIC Additionally, it includes information about the different products available in the chain.
# MAGIC ```
# MAGIC
# MAGIC 4. Add the tables from your schema:
# MAGIC    - `fct_coffee_shop_transactions`
# MAGIC    - `fct_coffee_shop_stores_reviews_sentiment`
# MAGIC    - `dim_coffee_shop_stores`
# MAGIC    - `dim_coffee_products`
# MAGIC 5. Click **Save**
# MAGIC
# MAGIC **What to observe:**
# MAGIC - The description helps users understand what this Genie Space can answer
# MAGIC - Adding the right tables is critical — Genie can only query what you give it
# MAGIC - Focused datasets produce better results than adding every table in your schema

# COMMAND ----------

# DBTITLE 1,Exercise — Add General Instructions
# MAGIC %md
# MAGIC ### Exercise — Add General Instructions
# MAGIC
# MAGIC Instructions help Genie understand business context, formatting rules, and domain-specific meanings.
# MAGIC
# MAGIC 1. In the Genie Space, click **Settings** (gear icon) > **General Instructions**
# MAGIC 2. **Add** the following:
# MAGIC
# MAGIC ```
# MAGIC BUSINESS RULES AND CONTEXT:
# MAGIC - Address the user in the most formal way
# MAGIC - Any product with total sales below 800 is at risk of being removed from the Menu
# MAGIC - Stores should consider negative reviews very seriously
# MAGIC - Hours with less than 10,000 total sales could be removed from the schedule
# MAGIC - Customer satisfaction is very important for corporate
# MAGIC - Better customer experience is more important than total sales
# MAGIC - All data related to money (like sales or price) should be assumed as in US dollars
# MAGIC - The best product is the one with the highest sales
# MAGIC ```
# MAGIC
# MAGIC 3. Click **Save**
# MAGIC 4. **Test it:** Ask Genie `What products should we consider removing?` — it should use the 800 sales threshold from your instructions
# MAGIC
# MAGIC > **Key takeaway:** Instructions let you encode business logic that isn't in the data itself. The more context you give Genie, the more accurate the answers.

# COMMAND ----------

# DBTITLE 1,Exercise — Add Sample Questions
# MAGIC %md
# MAGIC ### Exercise — Add Sample Questions
# MAGIC
# MAGIC Sample questions guide users and help Genie understand the types of questions the space is designed for.
# MAGIC
# MAGIC 1. In **Settings** > **Sample Questions**, click **Add**
# MAGIC 2. Add these sample questions one at a time:
# MAGIC
# MAGIC ```
# MAGIC What is the best selling time for the chain?
# MAGIC ```
# MAGIC ```
# MAGIC How many reviews have a negative sentiment and what's their average score?
# MAGIC ```
# MAGIC ```
# MAGIC What products should we remove from the menu?
# MAGIC ```
# MAGIC ```
# MAGIC What are the total sales by store for 2023?
# MAGIC ```
# MAGIC ```
# MAGIC Which store has the best customer satisfaction based on reviews?
# MAGIC ```
# MAGIC
# MAGIC 3. Click **Save**
# MAGIC 4. **Test it:** Refresh the Genie Space — your sample questions should appear in the welcome screen as suggested starting points
# MAGIC
# MAGIC **Tips:**
# MAGIC - Sample questions also serve as training examples for Genie
# MAGIC - Phrase them the way a real business user would ask
# MAGIC - Cover different question types: counts, aggregations, comparisons, rankings

# COMMAND ----------

# DBTITLE 1,Exercise — Define Table Joins
# MAGIC %md
# MAGIC ### Exercise — Define Table Joins
# MAGIC
# MAGIC Joins tell Genie how your tables relate to each other. Without them, Genie may produce incorrect multi-table queries.
# MAGIC
# MAGIC Refer to the Entity Relationship Diagram in the section above and define the following 3 joins:
# MAGIC
# MAGIC 1. In **Settings** > **Table Joins** (or **Relationships**)
# MAGIC 2. Define these joins:
# MAGIC
# MAGIC | Left Table | Join Column | Right Table | Join Column |
# MAGIC |---|---|---|---|
# MAGIC | `fct_coffee_shop_transactions` | `store_id` | `dim_coffee_shop_stores` | `store_id` |
# MAGIC | `fct_coffee_shop_transactions` | `product_id` | `dim_coffee_products` | `product_id` |
# MAGIC | `fct_coffee_shop_stores_reviews_sentiment` | `store_id` | `dim_coffee_shop_stores` | `store_id` |
# MAGIC
# MAGIC 3. Click **Save**
# MAGIC 4. **Test it:** Ask `What are the total sales by store name?` — Genie should correctly join transactions with stores
# MAGIC
# MAGIC **Tips:**
# MAGIC - Without explicit joins, Genie might guess relationships, but explicit definitions ensure accuracy
# MAGIC - If Genie produces unexpected results (like too many rows), check your join definitions first

# COMMAND ----------

# DBTITLE 1,Exercise — Create Trusted Assets
# MAGIC %md
# MAGIC ### Exercise — Create Trusted Assets (SQL Examples)
# MAGIC
# MAGIC **Trusted assets** are pre-verified SQL queries that Genie can use as templates when a question matches. They guarantee correct results for critical business questions.
# MAGIC
# MAGIC 1. In **Settings** > **Trusted Assets** (or **SQL Examples**), click **Add**
# MAGIC 2. Add the following trusted assets:
# MAGIC
# MAGIC **Trusted Asset 1 — Top Products by Store:**
# MAGIC - **Question:** `What are the top 3 best selling products for a specific store?`
# MAGIC - **SQL:** Use the query from the **SQL Example 1** cell above
# MAGIC
# MAGIC **Trusted Asset 2 — Busiest Hour by Store:**
# MAGIC - **Question:** `What is the most crowded time for a specific store?`
# MAGIC - **SQL:** Use the query from the **SQL Example 2** cell above
# MAGIC
# MAGIC 3. Click **Save** after each one
# MAGIC 4. **Test it:** Ask `What are the top 3 products at Astoria Brews?` — Genie should use your trusted SQL and return accurate results
# MAGIC
# MAGIC > **Note:** Trusted assets are especially important for complex calculations that Genie might get wrong on its own. Add them for any query where accuracy is critical.

# COMMAND ----------

# DBTITLE 1,Exercise — Verify Genie Configuration
# MAGIC %md
# MAGIC ### Exercise — Verify Your Genie Space Configuration
# MAGIC
# MAGIC Run through this checklist to make sure everything is configured correctly:
# MAGIC
# MAGIC | Item | How to Check | Expected Result |
# MAGIC |---|---|---|
# MAGIC | Description set | Settings > General | Shows the coffee assistant description |
# MAGIC | Instructions added | Settings > General Instructions | Business rules visible (sales threshold, formatting, etc.) |
# MAGIC | Sample questions | Settings > Sample Questions | 5 questions visible in the welcome screen |
# MAGIC | Joins defined | Settings > Table Joins | 3 joins configured |
# MAGIC | Trusted assets | Settings > Trusted Assets | 2 SQL examples saved |
# MAGIC | Business rules work | Ask "What products should we remove?" | Uses 800 sales threshold |
# MAGIC | Joins work | Ask "Total sales by store name" | Shows store names correctly |
# MAGIC | Trusted SQL used | Ask "Top 3 products at Astoria Brews?" then check SQL tab | SQL matches your trusted asset |
# MAGIC
# MAGIC **Bonus challenges:**
# MAGIC - Add a trusted asset for the sentiment analysis query
# MAGIC - Add an instruction about seasonal trends or peak hours
# MAGIC - Create a sample question that combines transactions with reviews data
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.1
# MAGIC %md
# MAGIC ---
# MAGIC ### Using Your Genie Space
# MAGIC
# MAGIC Now that your Genie Space is fully configured, let's put it to the test! Open your Genie Space and work through the following exercises.
# MAGIC
# MAGIC ### Exercise 3.1 — Start Simple
# MAGIC
# MAGIC Open your Genie Space and type these questions one at a time:
# MAGIC
# MAGIC 1. `How many transactions do we have in total?`
# MAGIC 2. `How many stores does the chain have?`
# MAGIC 3. `Show me the first 10 products with their prices`
# MAGIC
# MAGIC **What to observe:**
# MAGIC - Genie responds with a table of results
# MAGIC - Click the **SQL** tab to see how Genie translated your question
# MAGIC - Notice how Genie uses the correct table joins automatically

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.2
# MAGIC %md
# MAGIC ### Exercise 3.2 — Ask Business Questions
# MAGIC
# MAGIC Try these questions that relate to real coffee chain analytics needs:
# MAGIC
# MAGIC 1. `What are the total sales by store?`
# MAGIC 2. `Which product category has the highest total quantity sold?`
# MAGIC 3. `What is the average transaction total by store?`
# MAGIC
# MAGIC **Tips:**
# MAGIC - Use the column names from the instructions if you know them — Genie matches more accurately
# MAGIC - If Genie asks for clarification, provide it
# MAGIC - Try rephrasing if the first result isn’t what you expected

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.3
# MAGIC %md
# MAGIC ### Exercise 3.3 — Follow-Up Questions & Drill-Downs
# MAGIC
# MAGIC Genie remembers the context of your conversation. Ask these questions **in sequence** (don’t start a new conversation between them):
# MAGIC
# MAGIC 1. `Show me total sales by product category`
# MAGIC 2. `Now filter to just the top 3 categories`
# MAGIC 3. `Break that down by store`
# MAGIC 4. `Which store had the highest growth in that top category?`
# MAGIC
# MAGIC > **Key takeaway:** You don’t need to repeat context. Genie remembers what you’ve been discussing.

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.4
# MAGIC %md
# MAGIC ### Exercise 3.4 — Sentiment & Reviews Deep Dive
# MAGIC
# MAGIC 1. `How many reviews do we have by sentiment?`
# MAGIC 2. `What is the average score for negative reviews?`
# MAGIC 3. `Which store has the most negative reviews?`
# MAGIC 4. `Show me the ratio of positive to negative reviews by store`
# MAGIC 5. `What products should we consider removing based on low sales?`

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.5
# MAGIC %md
# MAGIC ### Exercise 3.5 — Verify and Trust Results
# MAGIC
# MAGIC **Review the SQL:**
# MAGIC 1. Ask Genie: `What is the best selling time for the chain?`
# MAGIC 2. Click the **SQL** tab on the response
# MAGIC 3. Check:
# MAGIC    - Is it querying the right table (`fct_coffee_shop_transactions`)?
# MAGIC    - Are the time groupings correct?
# MAGIC    - Does the result match what you’d expect from the data?
# MAGIC
# MAGIC **Handle Ambiguity:**
# MAGIC 1. Try asking a deliberately vague question: `Tell me about sales`
# MAGIC 2. Notice how Genie interprets it — is it what you expected?
# MAGIC 3. Now be more specific: `What is the total sales amount by store name for 2023, sorted by sales descending?`
# MAGIC 4. Compare the two results
# MAGIC
# MAGIC > **Lesson:** Specificity matters. The more precise your question, the better the answer.
# MAGIC
# MAGIC **Provide Feedback:**
# MAGIC
# MAGIC If an answer doesn’t look right:
# MAGIC 1. **Thumbs down** the response (helps improve future answers)
# MAGIC 2. **Rephrase** with more detail
# MAGIC 3. **Correct Genie**: "That’s not right — I meant by month, not by day"

# COMMAND ----------

# DBTITLE 1,Lab 3 Exercise 3.6
# MAGIC %md
# MAGIC ### Exercise 3.6 — Free Exploration
# MAGIC
# MAGIC Come up with **5 questions of your own** that are relevant to the coffee chain business. Try to include:
# MAGIC
# MAGIC - [ ] A count or aggregation question
# MAGIC - [ ] A trend or time-based question
# MAGIC - [ ] A comparison between two stores or products
# MAGIC - [ ] A top-N ranking question
# MAGIC - [ ] A question that combines transactions with reviews
# MAGIC
# MAGIC **My Questions:**
# MAGIC
# MAGIC 1. _____________________________________
# MAGIC 2. _____________________________________
# MAGIC 3. _____________________________________
# MAGIC 4. _____________________________________
# MAGIC 5. _____________________________________