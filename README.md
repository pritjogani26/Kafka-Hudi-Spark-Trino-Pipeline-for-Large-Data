<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<h1>Kafka-Hudi-Spark-Trino-Pipeline-for-Large-Data</h1>
</head>
<body>
<h1><b>Kafka-Hudi-Spark-Trino-Pipeline-for-Large-Data</b></h1>
<p>A high-performance data pipeline using Kafka, Hudi, Spark, and Trino to process, store, and query large-scale datasets in real-time.</p>

<h2><u>Introduction</u></h2>
<p>The <b>Kafka to Hudi Streaming Pipeline</b> is designed to facilitate real-time data ingestion and processing using Kafka, Spark, and Hudi. The pipeline allows for the streaming of data from Kafka, processing it with Spark, and storing it in Hudi tables for efficient querying and analytics. The project also integrates <b>Trino</b> for fast SQL-based querying on the ingested Hudi data, enabling interactive analytics at scale. This pipeline supports both real-time and batch processing, making it ideal for handling large volumes of data with low-latency requirements.</p>

<h2><u>Kafka to Hudi Streaming Pipeline</u></h2>
<p>This project sets up a Kafka to Hudi streaming pipeline using Spark and Trino. The pipeline consists of a Kafka producer that sends data to Kafka, a Spark consumer that processes data and writes to Hudi, and Trino for querying the data.</p>

<h3><u>1. Set Up Docker Containers</u></h3>
<h4><u>Start Docker Containers</u></h4>
<p>Stop any existing containers and restart them in detached mode:</p>
<pre><code>docker-compose pull
docker-compose up -d</code></pre>

<h3><u>2. Generate Data As Needed [Optional]</u></h3>
<p>There is a <b>random_users.jsonl</b> file that contains 10 lakh records. If you want to generate more or fewer records, follow these steps:</p>

<h4><u>Redirect to Folder Path</u></h4>
<pre><code>cd /data_generate</code></pre>

<h4><u>Create and Activate Virtual Environment:</u></h4>
<pre><code>python -m venv venv
/venv/Scripts/activate</code></pre>

<h4><u>Install the Necessary Dependencies:</u></h4>
<pre><code>pip install -r requirements.txt</code></pre>

<h4><u>Generate Random User Data:</u></h4>
<pre><code>python generate_large_random_json.py</code></pre>

<h3><u>3. Run Kafka Consumer</u></h3>
<h4><u>Create a Topic for Receiving Data</u></h4>
<p>Create the Kafka topic (<b>new-topic</b>) to receive the data:</p>
<pre><code>docker exec -it kafka kafka-topics.sh --create --topic new-topic --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1</code></pre>

<h4><u>Run Consumer Code</u></h4>
<p>Submit the Spark streaming job to process the data and write it to Hudi:</p>
<pre><code>docker exec -it spark-hudi bash
spark-submit --master local[*] --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 --jars /opt/extra_jars/hudi-spark3.4-bundle_2.12-0.14.1.jar /consumer/streaming_user_consumer.py</code></pre>

<h3><u>4. Run Kafka Producer</u></h3>
<p>Run the Kafka producer to send data to the Kafka topic:</p>
<pre><code>docker exec spark-hudi python /producer/kafka_producer.py</code></pre>

<h3><u>5. Run Trino Queries</u></h3>
<h4><u>Start Trino and Connect to the Hudi Catalog</u></h4>
<p>Run Trino and connect to the Hudi catalog:</p>
<pre><code>docker exec -it trino trino --server http://localhost:8080 --catalog hudi --schema default</code></pre>

<h4><u>Example Queries:</u></h4>
<ol>
<li><b>List all tables</b> in the default schema:
<pre><code>SHOW TABLES;</code></pre>
</li>
<li><b>Count records</b> in the tables:
<pre><code>SELECT COUNT(*) FROM users_rt;</code></pre>
<pre><code>SELECT COUNT(*) FROM users_ro;</code></pre>
</li>
<li><b>Select specific records</b> from <i>users_ro</i> with filters:
<pre><code>SELECT id, firstname, city FROM users_ro WHERE country='India' AND state='Gujarat' AND city='Ahmedabad' LIMIT 10;</code></pre>
</li>
</ol>

<h3><u>6. Stop Docker Containers</u></h3>
<pre><code>docker-compose down</code></pre>
<br><br>

<h2><u>Hudi Configuration</u></h2>

<p>This <b>hudi_config.py</b> file contains configuration settings for writing data to a Hudi table. Below is a breakdown of the key configurations:</p>

<h4><u>Table Configuration</u></h4>
<table border="1">
<tr>
<th><b>Setting</b></th>
<th><b>Description</b></th>
</tr>
<tr>
<td><b>Table Name</b></td>
<td>The table name is set to <b>users</b>.</td>
</tr>
<tr>
<td><b>Record Key</b></td>
<td>The record key field is <b>id</b>.</td>
</tr>
<tr>
<td><b>Pre-Combine Field</b></td>
<td>The pre-combine field is <b>ingestion_time</b>, used to handle versioning of records.</td>
</tr>
<tr>
<td><b>Operation</b></td>
<td>The operation is set to <b>upsert</b>, meaning it will insert new records or update existing ones.</td>
</tr>
</table>

<h4><u>Partitioning</u></h4>
<table border="1">
<tr>
<th><b>Setting</b></th>
<th><b>Description</b></th>
</tr>
<tr>
<td><b>Partition Fields</b></td>
<td>Data is partitioned by <b>country</b>, <b>state</b>, and <b>city</b>.</td>
</tr>
<tr>
<td><b>Hive Style Partitioning</b></td>
<td>This is set to <b>false</b> (partitioning style is not based on Hive's typical format).</td>
</tr>
</table>

<h4><u>Metadata & Indexing</u></h4>
<table border="1">
<tr>
<th><b>Setting</b></th>
<th><b>Description</b></th>
</tr>
<tr>
<td><b>Metadata</b></td>
<td>Asynchronous metadata indexing is enabled for faster query performance.</td>
</tr>
<tr>
<td><b>Column Statistics</b></td>
<td>Statistics for columns like <b>firstname</b>, <b>email</b>, <b>country</b>, <b>state</b>, and <b>city</b> are included in the metadata.</td>
</tr>
<tr>
<td><b>Bloom Indexing</b></td>
<td>Bloom indexing is enabled to speed up lookups.</td>
</tr>
<tr>
<td><b>Bucket Indexing</b></td>
<td>Bucket indexing is set to <b>BUCKET</b>, with 8 buckets for better data distribution.</td>
</tr>
</table>

<h4><u>File Management</u></h4>
<table border="1">
<tr>
<th><b>Setting</b></th>
<th><b>Description</b></th>
</tr>
<tr>
<td><b>Parquet File Settings</b></td>
<td>The maximum size for Parquet files is set to 128MB (<b>134217728</b> bytes).</td>
</tr>
<tr>
<td><b>Parallelism</b></td>
<td>Insert and upsert parallelism are set to <b>4</b>, optimizing write operations.</td>
</tr>
</table>

<h4><u>Layout Optimization</u></h4>
<p>The data layout is optimized using a Z-order strategy on the <b>country</b>, <b>state</b>, and <b>city</b> columns. This helps in reducing query time for these columns.</p>

<h4><u>Clean & Compact</u></h4>
<p>Automatic cleaning of obsolete files is enabled, and inline compaction occurs after every 2 delta commits.</p>

<h4><u>Base Path</u></h4>
<p>The base path where the Hudi table is stored is set to <b>/hudi_output</b>.</p>

<h2><u>Dockerfile for Spark-Hudi</u></h2>
<p>This <b>Dockerfile</b> is used to build a custom image for the Spark-Hudi service. It uses the <b>bitnami/spark:3.4.1</b> base image, installs necessary dependencies, and prepares the working environment for Spark-Hudi integration with Kafka.</p>

<h2><u>Kafka to Hudi Streaming Consumer</u></h2>
<p>This script consumes data from a Kafka topic, processes it using PySpark, and writes it into a Hudi table. The script handles:</p>
<ul>
<li><b>Kafka Integration</b>: Consumes messages from the Kafka topic <b>new-topic</b>.</li>
<li><b>Data Processing</b>: Cleans data and adds ingestion time.</li>
<li><b>Hudi Write</b>: Writes processed data into a Hudi table.</li>
<li><b>Checkpointing</b>: Tracks streaming state.</li>
<li><b>Streaming</b>: Processes data in micro-batches.</li>
</ul>

<h2><u>Kafka Producer for User Data</u></h2>
<p>This script sends user data from a JSON Lines (jsonl) file to Kafka for further processing by the consumer.</p>
<ul>
<li><b>Data Loading</b>: Reads a JSONL file and sends it to Kafka.</li>
<li><b>Kafka Producer</b>: Initializes the producer and sends messages.</li>
</ul>
</body>
</html>
