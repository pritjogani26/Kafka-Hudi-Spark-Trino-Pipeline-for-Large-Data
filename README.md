# Kafka-Hudi-Spark-Trino-Pipeline-for-Large-Data
A high-performance data pipeline using Kafka, Hudi, Spark, and Trino to process, store, and query large-scale datasets in real-time.

# Introduction
    The Kafka to Hudi Streaming Pipeline is designed to facilitate real-time data ingestion and processing using Kafka, Spark, and Hudi. The pipeline allows for the streaming of data from Kafka, processing it with Spark, and storing it in Hudi tables for efficient querying and analytics. The project also integrates Trino for fast SQL-based querying on the ingested Hudi data, enabling interactive analytics at scale. This pipeline supports both real-time and batch processing, making it ideal for handling large volumes of data with low-latency requirements.

# Kafka to Hudi Streaming Pipeline
This project sets up a Kafka to Hudi streaming pipeline using Spark and Trino. The pipeline consists of a Kafka producer that sends data to Kafka, a Spark consumer that processes data and writes to Hudi, and Trino for querying the data.

## 1. **Set Up Docker Containers**

### Start Docker Containers
    Stop any existing containers and restart them in detached mode:
    ```bash
    docker-compose pull
    docker-compose up -d

## 2. **Generate Data As Needed [Optional]**
    There is random_users.jsonl file is present which contain already 10 lakhs Data. If you want to more or less then run this commands.
    ```bash
### Redirect to Folder Path 
    cd /data_generate
### Create and Activate virtual environment:
    python -m venv venv
    /venv/Scripts/activate
### Install the necessary dependencies:
    pip install -r requirements.txt
### Generate random user data:
    python generate_large_random_json.py

## 3. Run Kafka Consumer

### Create a topic for reaceive data
    docker exec -it kafka kafka-topics.sh --create --topic new-topic --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1
### Run Consumer Code
    docker exec -it spark-hudi bash
    spark-submit   --master local[*]   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1   --jars /opt/extra_jars/hudi-spark3.4-bundle_2.12-0.14.1.jar   /consumer/streaming_user_consumer.py

## 4. Run Kafka Producer
    docker exec spark-hudi python /producer/kafka_producer.py

## 5. Run Trino Queries

### Start Trino and Connect to the Hudi Catalog
    docker exec -it trino trino --server http://localhost:8080 --catalog hudi --schema default
### Example Queries:
    1. List all tables in the default schema:
    - SHOW TABLES;
    2. Count records in the tables:
    - SELECT COUNT(*) FROM users_rt;
    - SELECT COUNT(*) FROM users_ro;
    3. Select specific records from users_ro with filters:
    - SELECT id, firstname, city FROM users_ro WHERE country='India' AND state='Gujarat' AND city='Ahmedabad' LIMIT 10;

## 6. Stop Docker Containers
    docker-compose down


# Hudi Configuration

This `hudi_config.py` file contains configuration settings for writing data to a Hudi table. Below is a breakdown of the key configurations:

## Table Configuration
- **Table Name**: The table name is set to `users`.
- **Record Key**: The record key field is `id`.
- **Pre-Combine Field**: The pre-combine field is `ingestion_time`, used to handle versioning of records.
- **Operation**: The operation is set to `upsert`, meaning it will insert new records or update existing ones.

## Partitioning
- **Partition Fields**: Data is partitioned by `country`, `state`, and `city`.
- **Hive Style Partitioning**: This is set to `false` (partitioning style is not based on Hive's typical format).
- **Hive Sync**: Integration with Hive is enabled, and it uses the `hms` mode with the `users` table in the `default` database.

## Metadata & Indexing
- **Metadata**: Asynchronous metadata indexing is enabled for faster query performance.
- **Column Statistics**: Statistics for columns such as `firstname`, `email`, `country`, `state`, and `city` are included in the metadata.
- **Bloom Indexing**: Bloom indexing is enabled to speed up lookups.
- **Bucket Indexing**: Bucket indexing is set to `BUCKET`, with 8 buckets for better data distribution.

## File Management
- **Parquet File Settings**: The maximum size for Parquet files is set to 128MB (`134217728` bytes).
- **Parallelism**: Insert and upsert parallelism are set to `4`, optimizing write operations.
  
## Layout Optimization
- **Z-order**: The data layout is optimized using a Z-order strategy on the `country`, `state`, and `city` columns. This helps in reducing query time for these columns.

## Clean & Compact
- **Automatic Clean**: Automatic cleaning of obsolete files is enabled.
- **Compact**: Inline compaction occurs after every 2 delta commits.

## Base Path
- **Output Path**: The base path where the Hudi table is stored is set to `/hudi_output`.

This configuration ensures efficient writing to Hudi with optimized query performance and integration with Hive.

# Dockerfile for Spark-Hudi

This `Dockerfile` is used to build a custom image for the Spark-Hudi service.

- **Base Image**: Uses `bitnami/spark:3.4.1` as the base image for Spark.
- **Python & Dependencies**: Installs `pyspark` (version 3.4.1) and `kafka-python` for Kafka integration.
- **Folder Setup**: Creates necessary folders for scripts, configurations, and additional JARs.
- **File Copy**: Copies configuration files and JARs into the container.
- **Permissions**: Adjusts file ownership for the correct user (`1001`).
- **Working Directory**: Sets `/app` as the working directory for scripts and configurations.

This image is tailored to run Spark jobs with Hudi, integrated with Kafka for streaming data processing.


# Kafka to Hudi Streaming Consumer

This script is designed to consume data from a Kafka topic, process it using PySpark, and write it into a Hudi table.

### Key Components:

1. **Kafka Integration**: 
   - Consumes messages from the Kafka topic `new-topic` using the `kafka:9092` broker.
   - Processes JSON messages and applies a user schema to extract relevant fields like `id`, `firstname`, `lastname`, `email`, `phone`, `dob`, `address`, etc.

2. **Data Processing**:
   - The schema is defined using `StructType`, and `current_timestamp()` is added to each record to track the ingestion time.
   - Data is cleaned by replacing any non-alphanumeric characters in `country`, `state`, and `city` fields with underscores.
   - Default values ("unknown") are set for missing fields in `country`, `state`, and `city`.

3. **Hudi Write**:
   - The processed data is written to Hudi using the `HoodieSparkSessionExtension`.
   - Data is repartitioned and written in "append" mode to a specified Hudi table location (`HUDI_BASE_PATH`).
   - A cumulative batch count is updated, and partitions (based on `country`, `state`, `city`) are logged.

4. **Checkpointing**:
   - The script uses a checkpoint directory (`CHECKPOINT_DIR`) to track the state of the stream and ensure data consistency.

5. **Streaming**:
   - The data is processed in micro-batches with a trigger interval of 10 seconds.
   - In case of a failure during a batch write, the script logs the error and continues processing.

This script enables real-time streaming and ingestion of user data into Hudi for optimized querying.


# Kafka Producer for User Data

This script acts as a Kafka producer, sending user data from a JSON Lines (jsonl) file to a Kafka topic.

### Key Components:

1. **Data Loading**:
   - The `load_user_data` function reads a JSON Lines file (`random_users.jsonl`) line by line and yields each record.
   
2. **Kafka Producer**:
   - The `create_kafka_producer` function initializes a Kafka producer that connects to the Kafka broker (`kafka:9092`) and serializes messages to JSON format.
   
3. **Message Sending**:
   - The `send_messages` function sends the user records to the Kafka topic `new-topic`.
   - It prints a message every 100 records sent, and flushes the producer after all messages are sent.

### Execution:
- The script reads user data from `/data/random_users.jsonl`, creates a Kafka producer, and sends the records to the Kafka topic for further processing by the consumer.

This setup is designed for efficiently streaming large datasets to Kafka for real-time processing.

