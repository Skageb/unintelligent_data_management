#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from pymongo import MongoClient

MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
MONGO_DB = "dw"
MONGO_COLLECTION = "gtd"

def prepare_mongo():
    client = MongoClient(MONGO_URI)

    if MONGO_DB in client.list_database_names():
        client.drop_database(MONGO_DB)

    db = client[MONGO_DB]
    db.create_collection(MONGO_COLLECTION)
    db[MONGO_COLLECTION].create_index('eventid', unique = True)

    client.close()
    print("MongoDB is prepared.")

if __name__ == '__main__':
    prepare_mongo()
