# unintelligent_data_management
Repository for final project in IKT453 - (Un)intelligent datamanegement. Includes frontend for a data warehouse with 3 options (MySQL, MongoDB and Neo4j) for backend running on different DBMS systems.


## Port forwarding

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
