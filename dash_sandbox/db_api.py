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

#Collect data from aggregated country tables in DW for globe graph.
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

#Call to fetch the scoop incident, max or min for integer or float categories, most common or least common for varchar categories.
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
    

    



# ---------- MongoDB Endpoint ----------

#Fetch all rows from gtd collection
@app.get("/api/mongo/table_data")
def get_mongo_data():
    MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
    client = MongoClient(MONGO_URI)
    odb_db = client["dw"]
    collection = odb_db["gtd"]
    try:
        data = list(collection.find({}, {"_id": 0}))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Collect data from aggregated country collections in dw
@app.get("/api/mongo/by_country_data")
def get_by_country_data_mongo(stat_type:str):
    assert stat_type in ['ransom_demanded', 'ransom_paid', 'num_attacks']

    try:
        MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
        client = MongoClient(MONGO_URI)
        db = client["dw"]

        # Determine collection and field name
        if stat_type == 'num_attacks':
            collection = db["terror_by_country"]
            value_field = "number_of_attacks"
        else:
            collection = db["ransom_by_country"]
            value_field = stat_type

        # Aggregation: for each country, get the row with the latest year
        pipeline = [
            {"$sort": {"country_txt": 1, "year": -1}},  # sort each group by country then latest year
            {"$group": {
                "_id": "$country_txt",
                "year": {"$first": "$year"},
                "value": {"$first": f"${value_field}"}
            }},
            {"$project": {
                "country_txt": "$_id",
                stat_type: "$value",
                "_id": 0
            }}
        ]

        result = list(collection.aggregate(pipeline))
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Fetch document for spesified event_id. Information used in autogenerated repport.
@app.get('/api/mongo/get_report_col_from_event_id')
def get_report_col_mongo(event_id:int):
    MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
    client = MongoClient(MONGO_URI)
    odb_db = client["dw"]
    collection = odb_db["gtd"]
    
    doc = collection.find_one({"eventid": f"{event_id}"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Define which fields to cast
    int_fields = ['fatalities', 'wounded', 'ransom_demanded', 'ransom_paid']
    float_fields = ['latitude', 'longitude']

    for field in int_fields:
        if field in doc:
            doc[field] = int(float(doc[field]))


    for field in float_fields:
        if field in doc:
            doc[field] = float(doc[field])


    return doc
    

#Call to fetch the scoop incident, max or min for integer categories, most common or least common for varchar categories.
@app.get('/api/mongo/get_scoop')
def get_scoop_mongo(category: str, search_option: bool = Query(True)):
    MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"
    client = MongoClient(MONGO_URI)
    db = client["dw"]
    collection = db["gtd"]
    try:
        order = -1 if search_option else 1

        if category in ['fatalities', 'wounded', 'ransom_demanded', 'ransom_paid']:
            doc = collection.find({category: {"$ne": None}}, {"_id": 0, "eventid": 1, category: 1}).sort(category, order).limit(1)
            result = list(doc)
            if not result:
                raise HTTPException(status_code=404, detail="No data found")
            return {"value": result[0][category], "eventid": result[0]["eventid"]}

        else:
            pipeline = [
                {"$match": {category: {"$exists": True}}},
                {"$group": {"_id": f"${category}", "count": {"$sum": 1}}},
                {"$sort": {"count": order}},
                {"$limit": 1}
            ]
            agg_result = list(collection.aggregate(pipeline))

            if not agg_result:
                raise HTTPException(status_code=404, detail="No data found")

            value = agg_result[0]["_id"]
            match = collection.find_one({category: value}, {"_id": 0, "eventid": 1})
            return {"value": value, "eventid": match["eventid"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



    


    



# ---------- Neo4j Setup and Endpoints ----------
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"
driver = GraphDatabase.driver(uri, auth=(username, password))

#Get all unique terror groups.
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
    
#Get the 10 most active terror groups globally with each groups number of attacks
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

#Get number of attacks and most active terror group by country.
@app.get("/api/neo4j/get_attack_stats_on_country")
def neo_get_attack_stats_on_country():
    query = """
    MATCH (a:Incident)-[:HAPPENED_IN]->(c:Country)
    OPTIONAL MATCH (a)-[:COMMITED_BY]->(g:AttackGroup)
    WITH c.name AS country, COALESCE(g.name, "Unknown") AS group_name, COUNT(*) AS attack_count

    ORDER BY attack_count DESC
    WITH country, COLLECT({group: group_name, count: attack_count}) AS groups

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

#Get number of attacks by country for spesified group
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
    
# Get the 5 most common attack types for spesified terror group with number of attacks for each attack type
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

# Get the 5 most common cities attacked for spesified terror group with number of attacks in each city.
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

