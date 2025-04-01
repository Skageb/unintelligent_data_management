#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kafka import KafkaConsumer
from pymongo import MongoClient, errors
import csv
from io import StringIO

MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
MONGO_DB = "odb"
MONGO_COLLECTION = "gtd"

KAFKA_TOPIC = "Data"
KAFKA_BROKER = "127.0.0.1:29092"

input_fields = [
    "eventid", "year", "month", "day", "country", "country_txt", "region", "region_txt",
    "city", "success", "suicide", "attacktype", "attacktype_txt", "target_type",
    "target_type_txt", "victim_nat", "victim_nat_txt", "attacker_group", "motive",
    "weapon_type", "weapon_type_txt", "fatalities", "wounded", "ransom",
    "ransom_demanded", "ransom_paid"
]

def parse_kafka_line(line):
    reader = csv.reader(StringIO(line))
    values = next(reader)
    return dict(zip(input_fields, values))

def mongo_consumer():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    collection.create_index("eventid", unique=True)
    consumer = KafkaConsumer("Data", bootstrap_servers=KAFKA_BROKER, api_version=(2,0,2))

    print('\nWaiting for INPUT TUPLES, Ctr/Z to stop ...')

    batch = []
    batch_size = 1000
    total_inserted = 0

    for message in consumer:
        in_string = message.value.decode()
        if in_string == "DONE":
            print("\nProducer has finished sending data. Processing remaining tuples...")
            
            if batch:
                try:
                    collection.insert_many(batch, ordered=False)
                    total_inserted += len(batch)
                    print(f"Batch inserted. Total inserted: {total_inserted}")
                    print('\nWaiting for INPUT TUPLES, Ctr/Z to stop ...')
                except errors.BulkWriteError as bwe:
                    inserted_count = len(bwe.details.get("writeErrors", []))
                    total_inserted += len(batch) - inserted_count
                    print(f"Batch insert had duplicates. Total inserted: {total_inserted}")
                    break
        
        doc = parse_kafka_line(in_string)
        batch.append(doc)

        if len(batch) >= batch_size:
            try:
                collection.insert_many(batch, ordered=False)
                total_inserted += len(batch)
                print(f"Inserted {total_inserted} documents so far...")
            except errors.BulkWriteError as bwe:
                inserted_count = len(bwe.details.get("writeErrors", []))
                total_inserted += len(batch) - inserted_count
                print(f"Inserted {total_inserted} (some duplicates skipped)")
            batch.clear()

    

    client.close()

if __name__ == '__main__':
    while True:
        mongo_consumer()