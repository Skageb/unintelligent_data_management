from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import mysql.connector
import pandas as pd
from pymongo import MongoClient
from neo4j import GraphDatabase

app = FastAPI()

# Enable CORS (optional, useful for Dash)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MySQL Endpoint ----------
@app.get("/api/mysql_data")
def get_mysql_data():
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=13306,
            user='root',
            password='secret',
            database='odb'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM terrorism")
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- MongoDB Endpoint ----------
@app.get("/api/mongo_data")
def get_mongo_data():
    try:
        MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
        client = MongoClient(MONGO_URI)
        odb_db = client["odb"]
        collection = odb_db["gtd"]
        data = list(collection.find())
        for doc in data:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Neo4j Setup and Endpoints ----------
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"
driver = GraphDatabase.driver(uri, auth=(username, password))

@app.get("/api/neo4j_countries")
def get_neo4j_countries():
    try:
        with driver.session() as session:
            query = """
            MATCH (c:Country)
            RETURN c.name AS country
            """
            result = session.run(query)
            countries = [record['country'] for record in result]
            return countries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/neo4j_attacks")
def get_neo4j_attacks(country: str = Query(..., description="Country name to query")):
    try:
        with driver.session() as session:
            query = """
            MATCH (a:Incident)-[:HAPPENED_IN]->(c:Country)
            WHERE c.name = $country
            RETURN a.id AS attack_id, a.year AS year, a.city AS city, a.attack_type AS attack_type
            ORDER BY a.year DESC
            """
            result = session.run(query, country=country)
            attacks = []
            for record in result:
                attacks.append({
                    'attack_id': record['attack_id'],
                    'year': record['year'],
                    'city': record['city'],
                    'attack_type': record['attack_type']
                })
            return attacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
