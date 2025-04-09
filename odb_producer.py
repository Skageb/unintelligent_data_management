#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error
from kafka import KafkaProducer, KafkaConsumer

def odb_producer():
    # Connect to MySQL database
    odb_conn = None

    # dimension tables
    odb_query1 = "SELECT country, country_txt, region, region_txt, city, latitude, longitude " \
    "FROM terrorism " \
    "ORDER BY country_txt"

    odb_query2 = "SELECT target_type, target_type_txt " \
    "FROM terrorism " \
    "ORDER BY target_type"

    odb_query3 = "SELECT victim_nat, victim_nat_txt " \
    "FROM terrorism " \
    "ORDER BY victim_nat"

    odb_query4 = "SELECT weapon_type, weapon_type_txt " \
    "FROM terrorism " \
    "ORDER BY weapon_type_txt"

    odb_query5 = "SELECT attacktype, attacktype_txt " \
    "FROM terrorism " \
    "ORDER BY attacktype"

    # fact table    
    odb_query6 = "SELECT eventid, year, month, day, latitude, longitude, target_type, victim_nat, weapon_type, attacktype, success, suicide, fatalities, wounded, ransom_demanded, ransom_paid, attacker_group, motive " \
             "FROM terrorism " \
             "ORDER BY eventid"
    
    odb_query_mongo = "SELECT * FROM terrorism"

                          
    consumer = KafkaConsumer('odb-update-stream',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))                      
    producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
          
    print('\nWaiting for ODB UPDATE EVENT, Ctr/Z to stop ...')
    for message in consumer:
        print ('\nODB UPDATE EVENT RECEIVED FROM odb-update-stream')
        print ('Producing aggregated tuple for AggrData stream ...')
                
        break
                           
    try:  
        odb_conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=13306, 
                                  database = 'odb',
                                  user='deuser',
                                  password='depassword')
        
        if odb_conn.is_connected():
                print('\nConnected to source ODB MySQL database')

        # dimension tables
        # location_date   
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query1)
        location_tuples = odb_cursor.fetchall()
        for i in location_tuples:
            line = "L:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())

        # dim_target
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query2)
        target_tuples = odb_cursor.fetchall()
        for i in target_tuples:
            line = "T:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())

        # dim_nationality
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query3)
        nationality_tuples = odb_cursor.fetchall()
        for i in nationality_tuples:
            line = "N:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())

        # dim_weapon
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query4)
        weapon_tuples = odb_cursor.fetchall()
        for i in weapon_tuples:
            line = "W:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())

        # dim_attack
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query5)
        attack_tuples = odb_cursor.fetchall()
        for i in attack_tuples:
            line = "A:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())


        # fact_table
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query6)
        fact_terror_tuples = odb_cursor.fetchall()
        for i in fact_terror_tuples:
            line = "F:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())

        # mongo
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query_mongo)
        fact_terror_tuples = odb_cursor.fetchall()
        for i in fact_terror_tuples:
            line = ",".join(str(x) for x in i)
            producer.send('MongoData', line.encode())

        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_query_mongo)
        fact_terror_tuples = odb_cursor.fetchall()
        for i in fact_terror_tuples:
            line = ",".join(str(x) for x in i)
            producer.send('NeoData', line.encode())


        producer.send('AggrData', b"DONE")
        producer.flush()
        producer.send('MongoData', b"DONE")
        producer.flush()
        producer.send('NeoData', b"DONE")
        producer.flush()
            
    except Error as e:
        print(e)
        
    finally:
        if odb_conn is not None and odb_conn.is_connected():
            odb_cursor.close()
            odb_conn.close()
            
if __name__ == '__main__':
    while True:
        odb_producer()
    