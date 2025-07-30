# producer/producer.py
import json
import time
from kafka import KafkaProducer

def load_user_data(file_path):
    """Reads JSON Lines (jsonl) file and yields one record at a time"""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def create_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=["kafka:9092"],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

def send_messages(producer, topic, records):
    for i, record in enumerate(records, 1):
        producer.send(topic, record)
        if(i % 100) == 0:
            print(f"[{i}] Sent")
    producer.flush()
    print("All messages sent and flushed.")

if __name__ == "__main__":
    data_generator = load_user_data("/data/random_users.jsonl")
    producer = create_kafka_producer()
    send_messages(producer, "new-topic", data_generator)
