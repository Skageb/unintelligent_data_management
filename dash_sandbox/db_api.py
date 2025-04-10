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

#Get all data from odb
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

#Collect data from aggregated country tables in dw
@app.get("/api/mysql/by_country_data")
def get_by_country_data_sql(stat_type:str):
    assert stat_type in ['ransom_demanded', 'ransom_paid', 'num_attacks']
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=23306,
            user='root',
            password='secret',
            database='dw'
        )
        cursor = conn.cursor()
        if 'ransom' in stat_type:

            table_name = 'ransom_by_country'
            col_of_interest = stat_type
        
        elif stat_type == 'num_attacks':
            table_name = 'terror_by_country'
            col_of_interest = 'number_of_attacks'

        #Flexible query for similar tables in dw
        query = f"""SELECT t.country_txt, t.{col_of_interest}
                    FROM {table_name} AS t
                    WHERE t.year = (
                        SELECT MAX(t2.year)
                        FROM {table_name} AS t2
                        WHERE t2.country_txt = t.country_txt
                    )"""
        
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        return df.to_dict(orient='records')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Get colums by joining fact table with dimension tables used to generate the terror report
@app.get('/api/mysql/get_report_col_from_event_id')
def get_report_col_sql(event_id:int):
    query = f"""
    SELECT f.event_id, 
        f.group_name AS attacker_group, 
        f.latitude, 
        f.longitude, 
        f.motive, 
        f.ransom_demanded, 
        f.ransom_paid, 
        f.wounded, 
        f.fatalities, 
        f.date,
        l.city, 
        l.country_txt, 
        a.attack_desc AS attacktype_txt, 
        w.weapon_desc AS weapon_type_txt 
    FROM fact_terror_event f 
    LEFT JOIN dim_location l 
        ON f.latitude = l.latitude AND f.longitude = l.longitude 
    LEFT JOIN dim_attack_type a 
        ON f.attack_code = a.attack_code 
    LEFT JOIN dim_weapon_type w 
        ON f.weapon_code = w.weapon_code 
    WHERE f.event_id = {event_id}"""
    
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=23306,
        user='root',
        password='secret',
        database='dw'
    )
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)
    return df.to_dict(orient='records')

#Call to fetch the scoop incident, max or min for integer values, most common or least common for varchar values.
@app.get('/api/mysql/get_scoop')
def get_scoop_sql(category: str, search_option: bool = Query(True)):
    agg_func = 'MAX' if search_option else 'MIN'
    if category in ['fatalities', 'wounded', 'ransom_demanded', 'ransom_paid']:
        query = f"""
            SELECT f.{category} as value, f.event_id
            FROM fact_terror_event as f
            WHERE f.{category} = (
                SELECT {agg_func}(f.{category})
                FROM fact_terror_event f
            )
            LIMIT 1;
        """ 
    
    else:
    
        if category == 'attack_desc':
            table = 'dim_attack_type'
            join_att = 'attack_code'
        
        elif category == 'weapon_desc':
            table = 'dim_weapon_type'
            join_att = 'weapon_code'

        elif category == 'target_desc':
            table = 'dim_target'
            join_att = 'target_code'
        
        order = "DESC" if search_option else "ASC"

        
        query = f"""
            SELECT f.event_id, d.{category} AS value
            FROM fact_terror_event f
            JOIN {table} d ON f.{join_att} = d.{join_att}
            WHERE d.{category} = (
                SELECT d2.{category}
                FROM fact_terror_event f2
                JOIN {table} d2 ON f2.{join_att} = d2.{join_att}
                GROUP BY d2.{category}
                ORDER BY COUNT(*) {order}
                LIMIT 1
            )
            LIMIT 1;
        """
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=23306,
        user='root',
        password='secret',
        database='dw'
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return {"error": "No data found"}

    return {
        "value": result["value"],
        "event_id": result["event_id"]
    }
    



    

#Get all collum names from dw
@app.get("/api/mysql/all_attributes")
def get_all_attributes_sql():
    query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME IN ('dim_attack_type', 'dim_location', 'dim_nationality', 'dim_target', 'dim_weapon_type', 'fact_terror_event')
            """
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=23306,
            user='root',
            password='secret',
            database='dw'
        )
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        df = df.drop_duplicates()
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
    

@app.get("/api/neo4j/group_top_attack_types")
def get_group_attack_types_from_db(group_name: str):
    query = """
    MATCH (g:AttackGroup {name: $group_name})<-[:COMMITED_BY]-(a:Incident)-[:OF_TYPE]->(t:AttackType)
    WHERE NOT t.name = 'Unknown'
    RETURN t.name AS attack_type, COUNT(a) AS attack_count
    ORDER BY attack_count DESC
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, group_name=group_name)
        return [dict(record) for record in result]

@app.get("/api/neo4j/group_city")
def get_cities_for_group(group_name: str):
    query = """
    MATCH (g:AttackGroup {name: $group_name})<-[:COMMITED_BY]-(a:Incident)
    WHERE a.city IS NOT NULL AND NOT a.city = 'Unknown'
    RETURN a.city AS city, COUNT(a) AS attack_count
    ORDER BY attack_count DESC
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, group_name=group_name)
        return [dict(record) for record in result]

