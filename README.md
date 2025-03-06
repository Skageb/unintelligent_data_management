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
| ssh    | TCP        | 127.0.0.1     | 2222     |      | 22        |

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
```

Starting the application

```bash
python dash_sandbox/app.py
```

The application starts running at localhost:8080

The MySQL databases can be populated using the files

 - dw_consumer.py
 - odb_producer.py
 - odb_consumer.py
 - data_producer.py

