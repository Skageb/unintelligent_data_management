from kafka import KafkaConsumer, KafkaProducer
from neo4j import GraphDatabase

uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))

def escape_string(s):
    if isinstance(s, str):
        return s.replace("'", "").replace(",", ";")
    return ""

# Cipher query
def insert_into_neo4j(tx, batch):
    query = """
    UNWIND $batch AS event
    MERGE (a:Incident {id: event.attack_id})
    SET a.year = event.year, a.city = event.city, a.attack_type = event.attack_type, a.attack_group = event.attack_group
    MERGE (c:Country {name: event.country})
    MERGE (t:AttackType {name: event.attack_type})
    MERGE (g:AttackGroup {name: event.attack_group})
    MERGE (a)-[:HAPPENED_IN]->(c)
    MERGE (a)-[:OF_TYPE]->(t)
    MERGE (g)-[:COMMITS_TERROR_IN]->(c)
    MERGE (a)-[:COMMITED_BY]->(g)
    """
    tx.run(query, batch=batch)

# Execute database transaction
def process_batch(batch):
    try:
        with driver.session() as session:
            session.execute_write(insert_into_neo4j, batch)
            print(f"Inserted batch of {len(batch)} records into Neo4j")
    except Exception as e:
        print(f"Error inserting batch: {e}")

consumer = KafkaConsumer(
    'NeoData',
    bootstrap_servers='127.0.0.1:29092',
    api_version=(2, 0, 2),
)

producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')

# Listen to Kafka and insert to neo4j database
def consume_and_insert():
    print("Consuming Kafka messages...")

    batch = []

    for message in consumer:
        message_value = message.value.decode('utf-8')

        if message_value == "DONE":
            print("Producer finished sending data. Processing remaining batch...")
            # Insert incomplete batch
            if batch:
                process_batch(batch)

            print("All messages processed.")
            break

        fields = message_value.split(',')

        if len(fields) < 26:
            print(f"Skipping malformed message: {message_value}")
            continue

        # Insert in batches of 1000
        try:
            attack_id = fields[0]
            year = int(fields[1])
            city = escape_string(fields[8])
            country = escape_string(fields[5])
            attack_type = escape_string(fields[14])
            attack_group = escape_string(fields[19])

            batch.append({
                "attack_id": attack_id,
                "year": year,
                "city": city,
                "country": country,
                "attack_type": attack_type,
                "attack_group": attack_group
            })

            if len(batch) >= 1000:
                process_batch(batch)
                batch.clear()

        except ValueError as e:
            print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == '__main__':
    while True:
        consume_and_insert()
