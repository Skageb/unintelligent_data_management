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
from kafka import KafkaConsumer

def dw_consumer():
    # Connect to MySQL database
    dw_conn = None
    dw_load_query1 = "INSERT INTO fatalities(year,fatalities) " \
                     "VALUES(%s,%s)"
    
    dw_load_query2 = "INSERT INTO ransom_by_country(country, country_txt, ransom_demanded, ransom_paid) " \
                     "VALUES(%s,%s,%s,%s)"
    
    dw_load_query3 = "INSERT INTO terror_in_norway(year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive) " \
                     "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    
    dw_load_query4 = "INSERT INTO weapon_type(weapon_type, weapon_type_desc, fatalities, wounded, occurences) " \
                     "VALUES(%s,%s,%s,%s,%s)"
    
    
    consumer = KafkaConsumer('AggrData',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
    
    print('\nWaiting for AGGREGATED TUPLES, Ctr/Z to stop ...')
    
    fatalities_tuples = [] 
    ransom_tuples = []
    norway_tuples = []
    weapon_tuples = []

    for message in consumer:
        in_string = message.value.decode()

        if in_string == "DONE":
            print("\nProducer has finished sending data. Processing remaining tuples...")
            break

        if in_string.startswith("F:"):
            data = in_string[2:].split(',')
            try: 
                year = int(data[0].strip())
                fatalities = int(data[1].strip())
                fatalities_tuples.append((year, fatalities))
                print("\nFatalities Tuple Received: ({}, {})".format(year, fatalities))
            except Exception as e:
                print("Error processing fatalities data:", e)
        elif in_string.startswith("R:"):
            data = in_string[2:].split(',')
            try:
                country = data[0].strip()
                country_txt = data[1].strip()
                total_ransom_demanded = int(data[2].strip())
                total_ransom_paid = int(data[3].strip())
                ransom_tuples.append((country, country_txt, total_ransom_demanded, total_ransom_paid))
                print("\nRansom Tuple Received: ({}, {}, {}, {})".format(country, country_txt, total_ransom_demanded, total_ransom_paid))
            except Exception as e:
                print("Error processing ransom data:", e)
        elif in_string.startswith("N:"):
            data = in_string[2:].split(',')
            try:
                year = data[0].strip()
                city = data[1].strip()
                fatalities = int(data[2].strip())
                wounded = int(data[3].strip())
                success = int(data[4].strip())
                suicide = int(data[5].strip())
                attacker_group = data[6].strip()
                target_type = data[7].strip()
                weapon_type = data[8].strip()
                motive = data[9].strip()
                norway_tuples.append((year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive))
                print("\nNorway Tuple Received: ({}, {}, {}, {}, {}, {}, {}, {}, {})".format(year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive))
            except Exception as e:
                print("Error processing ransom data:", e)
        elif in_string.startswith("W:"):
            data = in_string[2:].split(',')
            try:
                weapon_type = int(data[0].strip())
                weapon_type_txt = data[1].strip()
                fatalities = int(data[2].strip())
                wounded = int(data[3].strip())
                eventid = int(data[4].strip())
                weapon_tuples.append((weapon_type, weapon_type_txt, fatalities, wounded,eventid))
                print("\nWeapon Tuple Received: ({}, {}, {}, {}, {})".format(weapon_type, weapon_type_txt, fatalities, wounded,eventid))
            except Exception as e:
                print("Error processing ransom data:", e)

    
    try:  
        dw_conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=23306, 
                                  database = 'dw',
                                  user='deuser',
                                  password='depassword')
        
        if dw_conn.is_connected():
                print('\nConnected to destination DW MySQL database')
        
        dw_cursor = dw_conn.cursor()
    
        dw_cursor.executemany(dw_load_query1, fatalities_tuples)
        dw_cursor.executemany(dw_load_query2, ransom_tuples)
        dw_cursor.executemany(dw_load_query3, norway_tuples)
        dw_cursor.executemany(dw_load_query4, weapon_tuples)
        
        dw_conn.commit()
        
        dw_cursor.execute("SELECT count(*) FROM fatalities")
        fatalities_count = dw_cursor.fetchone()[0]

        dw_cursor.execute("SELECT count(*) FROM ransom_by_country")
        ransom_count = dw_cursor.fetchone()[0]

        dw_cursor.execute("SELECT count(*) FROM terror_in_norway")
        norway_count = dw_cursor.fetchone()[0]

        dw_cursor.execute("SELECT count(*) FROM weapon_type")
        weapon_count = dw_cursor.fetchone()[0]

        print('DW is loaded: {} total fatalities records inserted'.format(fatalities_count))
        print('              {} total ransom records are inserted'.format(ransom_count))
        print('              {} total norway records are inserted'.format(norway_count))
        print('              {} total weapon records are inserted'.format(weapon_count))

            
    except Error as e:
        print(e)
        
    finally:
        if dw_conn is not None and dw_conn.is_connected():
            dw_cursor.close()
            dw_conn.close()    
            
if __name__ == '__main__':
    dw_consumer()
    