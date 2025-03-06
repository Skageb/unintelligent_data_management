import pandas as pd
from neo4j import GraphDatabase

uri = "neo4j://localhost:7687"
username = "neo4j"  # or your custom username
password = "password"

gtd_df = pd.read_csv("gtd.csv", low_memory=False).head(3)

driver = GraphDatabase.driver(uri, auth=(username, password))

def create_terrorism_graph():
    with driver.session() as session:
        for _, row in gtd_df.iterrows():
            # Example: Create nodes for each incident and its attributes
            attack_id = row.get('eventid')
            country = row.get('country_txt')
            attack_type = row.get('attacktype1_txt')
            year = row.get('iyear')
            city = row.get('city')

            # Handle missing city and escape single quotes in city, country, and attack_type
            city = city.replace("'", "''") if isinstance(city, str) else ""
            country = country.replace("'", "''") if isinstance(country, str) else ""
            attack_type = attack_type.replace("'", "''") if isinstance(attack_type, str) else ""

            # Construct the query with proper escaping
            query = (
                f"MERGE (a:Incident {{id: {attack_id}, year: {year}, city: '{city}', country: '{country}', attack_type: '{attack_type}'}})"
                f"MERGE (c:Country {{name: '{country}'}})"
                f"MERGE (t:AttackType {{name: '{attack_type}'}})"
                f"MERGE (a)-[:HAPPENED_IN]->(c)"
                f"MERGE (a)-[:OF_TYPE]->(t)"
            )
            
            try:
                # Run the query
                session.run(query)
            except Exception as e:
                print(f"Error processing {attack_id}: {e}")

# Call the function to create the graph in Neo4j with the first 3 rows
create_terrorism_graph()