import pandas as pd
from neo4j import GraphDatabase

uri = "neo4j://localhost:7687"
username = "neo4j"  # or your custom username
password = "password"

gtd_df = pd.read_csv("gtd.csv", low_memory=False).head(10000)

driver = GraphDatabase.driver(uri, auth=(username, password))

def escape_string(s):
    return s.replace("'", "") if isinstance(s, str) else ""
    
def insert_into_neo4j(tx, batch):
    query = """
    UNWIND $batch AS event
    MERGE (a:Incident {id: event.attack_id})
    SET a.year = event.year, a.city = event.city, a.country = event.country, a.attack_type = event.attack_type
    MERGE (c:Country {name: event.country})
    MERGE (t:AttackType {name: event.attack_type})
    MERGE (a)-[:HAPPENED_IN]->(c)
    MERGE (a)-[:OF_TYPE]->(t)
    """
    tx.run(query, batch=batch)

def create_terrorism_graph():
    batch = []
    with driver.session() as session:
        for _, row in gtd_df.iterrows():
            # Example: Create nodes for each incident and its attributes
            attack_id = row.get('eventid')
            country = row.get('country_txt')
            attack_type = row.get('attacktype1_txt')
            year = row.get('iyear')
            city = row.get('city')

            # Handle missing city and escape single quotes in city, country, and attack_type
            city = escape_string(city) if city else ""
            country = escape_string(country) if country else ""
            attack_type = escape_string(attack_type) if attack_type else ""

            # Construct the query with proper escaping
            batch.append({
            "attack_id": attack_id,
            "year": year,
            "city": city,
            "country": country,
            "attack_type": attack_type
            })

            if len(batch) >= 1000:
                try:
                    session.execute_write(insert_into_neo4j, batch)
                except Exception as e:
                    print(f"Failed to insert: {e}")
                batch.clear()

        if batch:  
            try:
                session.execute_write(insert_into_neo4j, batch)
                print(f"Inserted {len(batch)} records into Neo4j")
            except Exception as e:
                print(f"Failed to insert: {e}")

# Call the function to create the graph in Neo4j with the first 3 rows
create_terrorism_graph()