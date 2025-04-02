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


@app.get("/api/neo4j/get_terror_groups")
def neo_get_all_groups():
    query = """
    MATCH (g:AttackGroup)
    WHERE NOT g.name = 'Unknown'
    RETURN DISTINCT g.name AS group_name
    ORDER BY group_name
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return [record["group_name"] for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/api/neo4j/top_10_groups")
def neo_get_all_groups():
    query = """
    MATCH (g:AttackGroup)<-[:COMMITED_BY]-(a:Incident)
    WHERE g.name <> "Unknown"  // Optional: exclude "Unknown" groups
    RETURN g.name AS group_name, COUNT(a) AS num_attacks
    ORDER BY num_attacks DESC
    LIMIT 10
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/neo4j/get_attack_stats_on_country")
def neo_get_attack_stats_on_country():
    query = """
    // Step 1: Count attacks per (country, group)
    MATCH (a:Incident)-[:HAPPENED_IN]->(c:Country)
    OPTIONAL MATCH (a)-[:COMMITED_BY]->(g:AttackGroup)
    WITH c.name AS country, COALESCE(g.name, "Unknown") AS group_name, COUNT(*) AS attack_count

    // Step 2: Group them by country and sort to get the top group per country
    ORDER BY attack_count DESC
    WITH country, COLLECT({group: group_name, count: attack_count}) AS groups

    // Step 3: Extract top group + total attacks
    RETURN 
        country,
        REDUCE(s = 0, g IN groups | s + g.count) AS total_attacks,
        CASE
            WHEN groups[0].group = 'Unknown' AND size(groups) > 1 THEN groups[1].group
            ELSE groups[0].group
        END AS most_active_group
    """
    with driver.session() as session:
        result = session.run(query)
        data = [dict(record) for record in result]
        return data


@app.get("/api/neo4j/group_attacks_by_country")
def get_group_attacks_by_country(group_name: str):
    query = """
    MATCH (g:AttackGroup {name: $group_name})<-[:COMMITED_BY]-(a:Incident)-[:HAPPENED_IN]->(c:Country)
    RETURN c.name AS country, COUNT(a) AS attack_count
    ORDER BY attack_count DESC
    """
    with driver.session() as session:
        result = session.run(query, group_name=group_name)
        return [dict(record) for record in result]