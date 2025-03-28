# Unintelligent Data Management
Repository for final project in IKT453 - (Un)intelligent datamanegement. Includes frontend for a data warehouse with 3 options (MySQL, MongoDB and Neo4j) for backend running on different DBMS systems.

## Installation

To get started. Run a linux virtual machine, and use the following port forwarding

### Port forwarding

| Name     | Protocol | Host IP  | Host Port| Guest IP | Guest Port |
|----------|----------|----------|----------|----------|----------|
| DW       | TCP      | 127.0.0.1     | 23306    |      | 23306     |
| DWClient | TCP      | 127.0.0.1     | 25000    |      | 25000     |
| ODB      | TCP      | 127.0.0.1     | 13306    |      | 13306     |
| ODBClient| TCP      | 127.0.0.1     | 15000    |      | 15000     |
| kafka    | TCP      | 127.0.0.1     | 29092    |      | 29092     |
| neo4j    | TCP      | 127.0.0.1     | 7687     |      | 7687      |
| neo4jClient | TCP   | 127.0.0.1     | 7474     |      | 7474      |
| MongoDB    | TCP    | 127.0.0.1     | 27017    |      | 27017     |
| MongoDBClient| TCP  | 127.0.0.1     | 8081     |      | 8081      |
| ssh    | TCP        | 127.0.0.1     | 2222     |      | 22        |

### Setting up SSH on your virtual machine

Run the following command to install ssh in your virtual machine:

```bash
sudo apt-get install openssh-server
```

You should now be able to access your virtual machine through ssh from your host machine terminal with the command:
```bash
ssh -p 2222 <VM-username>@localhost
```
Replace \<VM-username\> with the username you selected on your virtual machine during setup.

### On your virtual machine

```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo apt-get install virtualbox-guest-dkms
sudo apt-get install virtualbox-guest-utils
```

Create a MySQL user (In this project there should be a user with name: deuser, and password: depassword)

### Share folder

Create a folder on your VM and one on your host machine. Share the folder by using

```bash
sudo mount -t vboxsf <host_folder> <vm_folder>
```

### On your host machine

Install dependencies

```bash
pip install pandas
pip install kafka-python
pip install mysql-connector-python
pip install neo4j
pip install dash
pip install pymongo
pip install dash-bootstrap-components
pip install fastapi
pip install 'uvicorn[standard]'
```

Clone repository

```bash
git clone https://github.com/Skageb/unintelligent_data_management.git
```

Navigate to the root of the project. This should be in the folder that is shared between the host and VM.

Download the [Global Terrorism Database](https://www.start.umd.edu/data-tools/GTD) and add it to the root of the project as a .csv file.

To start the project the databases need to be prepared

```bash
python prepare_odb.py
python prepare_dw.py
python prepare_neo4j.py
python prepare_mongo.py
```

The application consists of a dash frontend with a fastapi endpoint to make database requests. The api must be up and running for the application to work.

Run the API in a terminal:
```bash
cd dash_sandbox/
uvicorn db_api:app --reload --port 5001
```

When the API is running, open another terminal and run:
```bash
python dash_sandbox/app.py
```

This starts the application running at localhost:8080

The MySQL databases can be populated using the files

 - dw_consumer.py
 - odb_producer.py
 - odb_consumer.py
 - neo4j_consumer.py
 - data_producer.py

