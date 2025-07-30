# generate_users_parallel.py

import os
import io
import orjson
import uuid
import random
from datetime import datetime
from faker import Faker
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from state_city import INDIAN_CITY_STATE, USA_CITY_STATE

COUNTRY_LOCALES = {
    "India": "en_IN",
    "USA": "en_US"
}

def generate_user_record(country):
    fake = Faker(COUNTRY_LOCALES[country])
    if country == "India":
        city = random.choice(list(INDIAN_CITY_STATE.keys()))
        state = INDIAN_CITY_STATE[city]
    elif country == "USA":
        city = random.choice(list(USA_CITY_STATE.keys()))
        state = USA_CITY_STATE[city]
    return {
        "id": str(uuid.uuid4()),
        "firstname": fake.first_name(),
        "lastname": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "dob": fake.date_of_birth(minimum_age=20, maximum_age=30).strftime("%Y-%m-%d"),
        "address": fake.address().replace("\n", ", "),
        "city": city,
        "state": state,
        "zipcode": fake.postcode(),
        "country": country
    }

def generate_records_batch(count):
    batch = []
    for _ in range(count):
        country = random.choice(list(COUNTRY_LOCALES.keys()))
        record = generate_user_record(country)
        batch.append(orjson.dumps(record).decode("utf-8"))
    return batch

def generate_jsonl_data_parallel(file_path, total_records, batch_size=10000):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    workers = multiprocessing.cpu_count()
    print(f"Using {workers} CPU cores for parallel generation...")
    print(f"Batch size: {batch_size}, Total records: {total_records}")
    
    with open(file_path, "w", encoding="utf-8") as f:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i in range(0, total_records, batch_size):
                count = min(batch_size, total_records - i)
                futures.append(executor.submit(generate_records_batch, count))

            for idx, future in enumerate(as_completed(futures), start=1):
                records = future.result()
                buffer = io.StringIO()
                buffer.write("\n".join(records) + "\n")
                f.write(buffer.getvalue())
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Written batch {idx}/{len(futures)}")

    print(f"\nDone! {total_records:,} records saved to:\n{file_path}")

def main():
    try:
        n = int(input("Enter number of records to generate: "))
        if n <= 0:
            print("Please enter a number greater than 0.")
            return
    except ValueError:
        print("Invalid input. Please enter an integer.")
        return

    output_path = "..//producer_data//random_users.jsonl"
    generate_jsonl_data_parallel(output_path, n)

if __name__ == "__main__":
    main()
