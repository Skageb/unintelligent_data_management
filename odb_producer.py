#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: vladimir
Make sure you have mysql-connector installed:
    pip install mysql-connector-python
Also, make sure you created a mysql user deuser with password depassword and granted your user all privileges    
"""

import mysql.connector
from mysql.connector import Error
from kafka import KafkaProducer, KafkaConsumer

def odb_producer():
    # Connect to MySQL database
    odb_conn = None

    odb_aggregate_query1 = """
    SELECT year,
           SUM(SUM(fatalities)) OVER (ORDER BY year) AS cumulative_fatalities
    FROM terrorism
    GROUP BY year
    ORDER BY year
"""

    odb_aggregate_query2 = """
    SELECT year,
           country,
           country_txt,
           SUM(SUM(ransom_demanded)) OVER (PARTITION BY country, country_txt ORDER BY year) AS cumulative_ransom_demanded,
           SUM(SUM(ransom_paid)) OVER (PARTITION BY country, country_txt ORDER BY year) AS cumulative_ransom_paid
    FROM terrorism
    WHERE ransom = 1
    GROUP BY year, country, country_txt
    ORDER BY country, year
""" 

    odb_aggregate_query3 = """
    SELECT year, city, fatalities, wounded, success, suicide,
           attacker_group, target_type_txt, weapon_type_txt, motive
    FROM terrorism
    WHERE country = 151
    ORDER BY fatalities DESC
""" 

    odb_aggregate_query4 = """
    SELECT year,
           weapon_type,
           weapon_type_txt,
           SUM(SUM(fatalities)) OVER (PARTITION BY weapon_type, weapon_type_txt ORDER BY year) AS cumulative_fatalities,
           SUM(SUM(wounded)) OVER (PARTITION BY weapon_type, weapon_type_txt ORDER BY year) AS cumulative_wounded,
           SUM(COUNT(eventid)) OVER (PARTITION BY weapon_type, weapon_type_txt ORDER BY year) AS cumulative_occurences
    FROM terrorism
    GROUP BY year, weapon_type, weapon_type_txt
    ORDER BY weapon_type, year
"""

 
     
                          
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

        # fatalities   
        odb_cursor = odb_conn.cursor()
        odb_cursor.execute(odb_aggregate_query1)
        fatalities_tuples = odb_cursor.fetchall()
        for i in fatalities_tuples:
            line = "F:" + ",".join(str(x) for x in (i[0], int(i[1])))
            producer.send('AggrData', line.encode())
            print("\nProduced aggregated fatalities tuple: {}".format(line))


        # ransom
        odb_cursor.execute(odb_aggregate_query2)
        ransom_tuples = odb_cursor.fetchall()
        for i in ransom_tuples:
            line = "R:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())
            print("\nProduced aggregated ransom tuple: {}".format(line))

        # norway
        odb_cursor.execute(odb_aggregate_query3)
        norway_tuples = odb_cursor.fetchall()
        for i in norway_tuples:
            line = "N:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())
            print("\nProduced aggregated norway tuple: {}".format(line))

        # norway
        odb_cursor.execute(odb_aggregate_query4)
        weapon_tuples = odb_cursor.fetchall()
        for i in weapon_tuples:
            line = "W:" + ",".join(str(x) for x in i)
            producer.send('AggrData', line.encode())
            print("\nProduced aggregated weapon tuple: {}".format(line))

        producer.send('AggrData', b"DONE")
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
    