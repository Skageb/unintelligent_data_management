from kafka import KafkaConsumer, KafkaProducer
from neo4j import GraphDatabase

uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))

def escape_string(s):
    if isinstance(s, str):
        return s.replace("'", "").replace(",", ";")  # Escape quotes and commas
    return ""

def insert_into_neo4j(attack_id, year, city, country, attack_type):
    query = (
        f"MERGE (a:Incident {{id: {attack_id}, year: {year}, city: '{city}', country: '{country}', attack_type: '{attack_type}'}})"
        f"MERGE (c:Country {{name: '{country}'}})"
        f"MERGE (t:AttackType {{name: '{attack_type}'}})"
        f"MERGE (a)-[:HAPPENED_IN]->(c)"
        f"MERGE (a)-[:OF_TYPE]->(t)"
    )
    
    try:
        with driver.session() as session:
            session.run(query)
            print(f"Inserted data for attack_id {attack_id} into Neo4j")
    except Exception as e:
        print(f"Error inserting data for attack_id {attack_id}: {e}")

consumer = KafkaConsumer(
    'Data',
    bootstrap_servers='127.0.0.1:29092',
    api_version=(2, 0, 2),
)

producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')

# Consume messages from Kafka and insert them into the Neo4j database
def consume_and_insert():
    print("Consuming Kafka messages...")

    tuples = []
    
    for message in consumer:
        message_value = message.value.decode('utf-8')
        
        if message_value == "DONE":
            print("Producer has finished sending data. Processing remaining tuples...")
            break

        fields = message_value.split(',')

        if len(fields) < 24:
            print(f"Skipping malformed message: {message_value}")
            continue

        try:
            attack_id = fields[0]
            year = int(fields[1])
            city = escape_string(fields[7])
            country = escape_string(fields[5])
            attack_type = escape_string(fields[12])

            insert_into_neo4j(attack_id, year, city, country, attack_type)
            tuples.append((attack_id, year, city, country, attack_type))

        except ValueError as e:
            print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    print(f"Total {len(tuples)} tuples processed.")

if __name__ == '__main__':
    consume_and_insert()
