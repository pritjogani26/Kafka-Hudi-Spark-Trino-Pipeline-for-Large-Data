# consumer_service/streaming_user_consumer.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, regexp_replace, when, lit
from pyspark.sql.types import StructType, StructField, StringType
import time, os, sys

sys.path.append("/app/configs")
from hudi_config import HUDI_OPTIONS, HUDI_BASE_PATH  # type: ignore

KAFKA_TOPIC = "new-topic"
CHECKPOINT_DIR = f"/app/checkpoints/{KAFKA_TOPIC}"
COUNTER_FILE = "/app/batch_count.txt"

def update_cumulative_count(batch_count: int) -> int:
    total = 0
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            try:
                total = int(f.read().strip())
            except ValueError:
                total = 0
    total += batch_count
    with open(COUNTER_FILE, "w") as f:
        f.write(str(total))
    return total

# Define user schema
user_schema = StructType([
    StructField("id", StringType(), True),
    StructField("firstname", StringType(), True),
    StructField("lastname", StringType(), True),
    StructField("email", StringType(), True),
    StructField("phone", StringType(), True),
    StructField("dob", StringType(), True),
    StructField("address", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("zipcode", StringType(), True),
    StructField("country", StringType(), True),
])

with open(COUNTER_FILE, "w") as f:
    f.write("0")

# spark = SparkSession.builder \
#     .appName("KafkaToHudiStreaming") \
#     .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
#     .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
#     .config("spark.jars", "E:/Trino_Table/jars/hudi-spark3.4-bundle_2.12-0.14.1.jar") \
#     .config("spark.sql.shuffle.partitions", "2") \
#     .config("spark.driver.memory", "2g") \
#     .config("spark.executor.memory", "2g") \
#     .getOrCreate()

spark = SparkSession.builder \
    .appName("KafkaToHudiStreaming") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
    .config("spark.jars", "../Trino_Table/jars/hudi-spark3.4-bundle_2.12-0.14.1.jar") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.executor.cores", "1") \
    .config("spark.sql.broadcastTimeout", "300") \
    .config("spark.sql.autoBroadcastJoinThreshold", "10485760") \
    .getOrCreate()


spark.sparkContext.setLogLevel("ERROR")

kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

json_df = kafka_df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), user_schema).alias("data")) \
    .select("data.*") \
    .withColumn("ingestion_time", current_timestamp()) \
    .withColumn("country", when(col("country").isNull(), lit("unknown")).otherwise(col("country"))) \
    .withColumn("state", when(col("state").isNull(), lit("unknown")).otherwise(col("state"))) \
    .withColumn("city", when(col("city").isNull(), lit("unknown")).otherwise(col("city"))) \
    .withColumn("country", regexp_replace("country", "[^a-zA-Z0-9-_]", "_")) \
    .withColumn("state", regexp_replace("state", "[^a-zA-Z0-9-_]", "_")) \
    .withColumn("city", regexp_replace("city", "[^a-zA-Z0-9-_]", "_"))

def write_to_hudi(df, batch_id):
    df.persist()
    count = df.count()
    if count == 0:
        print(f"[Batch {batch_id}] Empty batch. Skipping write.")
        df.unpersist()
        return

    print(f"[Batch {batch_id}] Writing {count} records to Hudi...")

    df = df.repartition(2)

    try:
        df.write.format("hudi") \
            .options(**HUDI_OPTIONS) \
            .mode("append") \
            .save(HUDI_BASE_PATH)

        partitions_written = df.select("country", "state", "city").distinct().count()
        total = update_cumulative_count(count)
        print(f"[Batch {batch_id}] Write complete | Partitions: {partitions_written} | Total records: {total}")
    except Exception as e:
        print(f"[Batch {batch_id}] Write failed: {e}")
    finally:
        df.unpersist()

query = json_df.writeStream \
    .trigger(processingTime="10 seconds") \
    .foreachBatch(write_to_hudi) \
    .outputMode("update") \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .start()

try:
    print(f"Streaming started on topic: {KAFKA_TOPIC}")
    query.awaitTermination()
except Exception as e:
    print(f"Error during streaming: {e}")
    query.stop()
    spark.stop()
