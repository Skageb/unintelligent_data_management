#!/usr/bin/env python3

import csv
from pymongo import MongoClient

MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
ODB_NAME = "odb"
ODB_COLLECTION = "gtd"
CSV_FILE = "gtd.csv"

def main():
    client = MongoClient(MONGO_URI)
    db = client[ODB_NAME]
    collection = db[ODB_COLLECTION]

    with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        documents = list(reader)

    if documents:
        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents into {ODB_NAME}.{ODB_COLLECTION}.")
    else:
        print("No documents found in the CSV file. Nothing inserted.")

if __name__ == "__main__":
    main()
