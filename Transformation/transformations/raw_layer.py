from pyspark import pipelines as dp
from pyspark.sql.types import StructType, StructField, StringType

@dp.table()
def fct_coffee_shop_transactions():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .load(f"{spark.conf.get('param.volume')}/Transactions")
    )

@dp.table()
def dim_coffee_shop_stores():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("sep", ";")
        .load(f"{spark.conf.get('param.volume')}/Stores")
    )


@dp.table()
def fct_coffee_shop_stores_reviews():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .load(f"{spark.conf.get('param.volume')}/Customers")
    )

@dp.table()
def dim_coffee_products():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .load(f"{spark.conf.get('param.volume')}/Products")
    )