from kafka import KafkaConsumer, KafkaProducer
from neo4j import GraphDatabase

# Neo4j connection details
uri = "neo4j://localhost:7687"
username = "neo4j"  # or your custom username
password = "password"

# Create a driver instance to connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(username, password))

# Function to escape string to prevent issues with special characters in queries
def escape_string(s):
    if isinstance(s, str):
        return s.replace("'", "").replace(",", ";")  # Escape quotes and commas
    return ""

# Function to insert data into Neo4j
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

# Kafka consumer setup
consumer = KafkaConsumer(
    'Data',  # Kafka topic name
    bootstrap_servers='127.0.0.1:29092',  # Kafka broker address
    api_version=(2, 0, 2),  # Kafka API version
)

producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')

# Function to consume messages from Kafka and insert them into Neo4j
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
            attack_id = fields[0]  # eventid
            year = int(fields[1])  # iyear
            city = escape_string(fields[7])  # city
            country = escape_string(fields[5])  # country_txt
            attack_type = escape_string(fields[11])  # attacktype1_txt

            # Insert the data into Neo4j
            insert_into_neo4j(attack_id, year, city, country, attack_type)
            tuples.append((attack_id, year, city, country, attack_type))

        except ValueError as e:
            print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    print(f"Total {len(tuples)} tuples processed.")
    
    # Send a Kafka message to indicate completion
    try:
        m = 'neo4j update event'
        producer.send('neo4j-update-stream', m.encode())
        print('Neo4j update event sent to Neo4j update stream.')
        producer.flush()
    except Exception as e:
        print(f"Error sending update event: {e}")

if __name__ == '__main__':
    consume_and_insert()
