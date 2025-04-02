#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make sure you have mysql-connector installed:
    pip install mysql-connector-python
Also, make sure you created a mysql user deuser with password depassword and granted your user all privileges    
"""

import mysql.connector
from mysql.connector import Error
from kafka import KafkaProducer, KafkaConsumer

def dw_summary_producer():
    # Connect to MySQL database
    dw_conn = None

    dw_aggregate_query1 = """
    SELECT year, 
        SUM(fatalities) OVER (ORDER BY year) AS cumulative_fatalities
    FROM (
        SELECT YEAR(date) AS year, SUM(fatalities) AS fatalities
        FROM fact_terror_event
        GROUP BY YEAR(date)
    ) AS yearly
    ORDER BY year
    """

    dw_aggregate_query2 = """
    SELECT year,
        country_code,
        country_txt,
        SUM(ransom_demanded) OVER (PARTITION BY country_code, country_txt ORDER BY year) AS cumulative_ransom_demanded,
        SUM(ransom_paid) OVER (PARTITION BY country_code, country_txt ORDER BY year) AS cumulative_ransom_paid
    FROM (
        SELECT YEAR(f.date) AS year,
            l.country_code,
            l.country_txt,
            SUM(f.ransom_demanded) AS ransom_demanded,
            SUM(f.ransom_paid) AS ransom_paid
        FROM fact_terror_event f
        JOIN dim_location l ON f.latitude = l.latitude AND f.longitude = l.longitude
        WHERE f.ransom_demanded > 0
        GROUP BY YEAR(f.date), l.country_code, l.country_txt
    ) AS yearly
    ORDER BY country_code, year
    """

    dw_aggregate_query3 = """
    SELECT YEAR(f.date), l.city, f.fatalities, f.wounded, f.success, f.suicide,
        f.group_name, t.target_desc, w.weapon_desc, f.motive
    FROM fact_terror_event f
    JOIN dim_location l ON f.latitude = l.latitude AND f.longitude = l.longitude
    JOIN dim_target t ON f.target_code = t.target_code
    JOIN dim_weapon_type w ON f.weapon_code = w.weapon_code
    WHERE l.country_code = 151
    ORDER BY f.fatalities DESC
    """

    dw_aggregate_query4 = """
    SELECT year,
        weapon_code,
        weapon_desc,
        SUM(fatalities) OVER (PARTITION BY weapon_code, weapon_desc ORDER BY year) AS cumulative_fatalities,
        SUM(wounded) OVER (PARTITION BY weapon_code, weapon_desc ORDER BY year) AS cumulative_wounded,
        SUM(occurences) OVER (PARTITION BY weapon_code, weapon_desc ORDER BY year) AS cumulative_occurences
    FROM (
        SELECT YEAR(f.date) AS year,
            f.weapon_code,
            w.weapon_desc,
            SUM(f.fatalities) AS fatalities,
            SUM(f.wounded) AS wounded,
            COUNT(f.event_id) AS occurences
        FROM fact_terror_event f
        JOIN dim_weapon_type w ON f.weapon_code = w.weapon_code
        GROUP BY YEAR(f.date), f.weapon_code, w.weapon_desc
    ) AS yearly
    ORDER BY weapon_code, year
    """


    consumer = KafkaConsumer('dw-update-stream', bootstrap_servers='127.0.0.1:29092', api_version=(2,0,2))                      
    producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092', api_version=(2,0,2))
          
    print('\nWaiting for DW UPDATE EVENT, Ctr/Z to stop ...')
    for message in consumer:
        print('\nDW UPDATE EVENT RECEIVED FROM dw-update-stream')
        print('Producing aggregated tuple for DwSummaryData stream ...')
        break
                           
    try:  
        dw_conn = mysql.connector.connect(host='127.0.0.1',
                                  port=23306, 
                                  database='dw',
                                  user='deuser',
                                  password='depassword')
        
        if dw_conn.is_connected():
            print('\nConnected to DW MySQL database')

        dw_cursor = dw_conn.cursor()

        # fatalities
        dw_cursor.execute(dw_aggregate_query1)
        fatalities_tuples = dw_cursor.fetchall()
        for i in fatalities_tuples:
            line = "D:" + ",".join(str(x) for x in (i[0], int(i[1])))
            producer.send('DwSummaryData', line.encode())

        # ransom
        dw_cursor.execute(dw_aggregate_query2)
        ransom_tuples = dw_cursor.fetchall()
        for i in ransom_tuples:
            line = "R:" + ",".join(str(x) for x in i)
            producer.send('DwSummaryData', line.encode())

        # norway
        dw_cursor.execute(dw_aggregate_query3)
        norway_tuples = dw_cursor.fetchall()
        for i in norway_tuples:
            line = "B:" + ",".join(str(x) for x in i)
            producer.send('DwSummaryData', line.encode())

        # weapon
        dw_cursor.execute(dw_aggregate_query4)
        weapon_tuples = dw_cursor.fetchall()
        for i in weapon_tuples:
            line = "C:" + ",".join(str(x) for x in i)
            producer.send('DwSummaryData', line.encode())

        producer.send('DwSummaryData', b"DONE")
        producer.flush()

    except Error as e:
        print(e)

    finally:
        if dw_conn is not None and dw_conn.is_connected():
            dw_cursor.close()
            dw_conn.close()
            
if __name__ == '__main__':
    while True:
        dw_summary_producer()
