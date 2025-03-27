#!/usr/bin/env python3

import mysql.connector
from pymongo import MongoClient

MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 13306,
    'user': 'deuser',
    'password': 'depassword',
    'database': 'odb'
}

def fetch_from_mysql():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM terrorism")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def insert_into_mongo(documents, batch_size=5000):
    client = MongoClient(MONGO_URI)
    db = client['odb']
    collection = db['gtd']
    collection.drop()

    total_docs = len(documents)

    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        try:
            collection.insert_many(batch, ordered=False)
        except Exception as e:
            print(f"Error inserting batch {i // batch_size + 1}: {e}")

        print(f"Inserted batch {i // batch_size + 1} ({len(batch)} documents)")
    
    print(f"Finished inserting all {total_docs} documents.")
    client.close()

def main():
    docs = fetch_from_mysql()
    insert_into_mongo(docs)

if __name__ == '__main__':
    main()