#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make sure you have mysql-connector installed:
    pip install mysql-connector-python
Also, make sure you created a mysql user deuser with password depassword and granted your user all privileges    
"""

import mysql.connector
from mysql.connector import Error
from kafka import KafkaConsumer
from kafka import KafkaProducer
import datetime

def dw_consumer():
    # Connect to MySQL database
    dw_conn = None
    
    dw_load_query1 = "INSERT IGNORE INTO dim_location(country_code, country_txt, region_code, region_name, city, latitude, longitude) " \
                      "VALUES(%s,%s,%s,%s,%s,%s,%s)"
    
    dw_load_query2 = "INSERT IGNORE INTO dim_target(target_code, target_desc) " \
                      "VALUES(%s,%s)"
    
    dw_load_query3 = "INSERT IGNORE INTO dim_nationality(victim_nationality_id, victim_nationality_desc) " \
                      "VALUES(%s,%s)"
    
    dw_load_query4 = "INSERT IGNORE INTO dim_weapon_type(weapon_code, weapon_desc) " \
                      "VALUES(%s,%s)"
    
    dw_load_query5 = "INSERT IGNORE INTO dim_attack_type(attack_code, attack_desc) " \
                      "VALUES(%s,%s)"
    
    dw_load_query6 = "INSERT INTO fact_terror_event(event_id, date, latitude, longitude, target_code, victim_nationality_id, weapon_code, attack_code, success, suicide, fatalities, wounded, ransom_demanded, ransom_paid, group_name, motive) " \
                      "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    
    
    consumer = KafkaConsumer('AggrData',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
    
    print('\nWaiting for AGGREGATED TUPLES, Ctr/Z to stop ...')
    
    dim_location_tuples = []
    dim_target_tuples = []
    dim_nationality_tuples = []
    dim_weapon_type_tuples = []
    dim_attack_type_tuples = []

    fact_terror_event_tuples = []

    for message in consumer:
        in_string = message.value.decode()

        if in_string == "DONE":
            print("\nProducer has finished sending data. Processing remaining tuples...")
            try:  
                dw_conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                        port=23306, 
                                        database = 'dw',
                                        user='deuser',
                                        password='depassword')
                
                if dw_conn.is_connected():
                        print('\nConnected to destination DW MySQL database')
                
                dw_cursor = dw_conn.cursor()
            
                dw_cursor.executemany(dw_load_query1, dim_location_tuples)
                dw_cursor.executemany(dw_load_query2, dim_target_tuples)
                dw_cursor.executemany(dw_load_query3, dim_nationality_tuples)
                dw_cursor.executemany(dw_load_query4, dim_weapon_type_tuples)
                dw_cursor.executemany(dw_load_query5, dim_attack_type_tuples)

                dw_cursor.executemany(dw_load_query6, fact_terror_event_tuples)

                
                dw_conn.commit()

                dw_cursor.execute("SELECT count(*) FROM dim_location")
                location_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_target")
                target_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_nationality")
                nationality_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_weapon_type")
                weapon_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_attack_type")
                attack_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM fact_terror_event")
                fact_count = dw_cursor.fetchone()[0]

                print('DW is loaded: {} total records inserted in fact table'.format(fact_count))
                print('              {} total records inserted in location table'.format(location_count))
                print('              {} total records inserted in target table'.format(target_count))
                print('              {} total records inserted in nationality table'.format(nationality_count))
                print('              {} total records inserted in weapon table'.format(weapon_count))
                print('              {} total records inserted in attack table'.format(attack_count))
        
            except Error as e:
                print(e)
                
            finally:
                if dw_conn is not None and dw_conn.is_connected():
                    dw_cursor.close()
                    dw_conn.close()

                producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')
                producer.send('dw-update-stream', b'dw update event')
                producer.flush()
                print('\nDW UPDATE EVENT SENT TO dw-update-stream')
            break

        # location dimension
        if in_string.startswith("L:"):
            data = in_string[2:].split(',')
            try: 
                country_code = int(data[0].strip())
                country_txt = data[1].strip()
                region_code = int(data[2].strip())
                region_name = data[3].strip()
                city = data[4].strip()
                latitude = data[5].strip()
                longitude = data[6].strip()
                dim_location_tuples.append((country_code, country_txt, region_code, region_name, city, latitude, longitude))
            except Exception as e:
                print("Error processing date:", e)

        # target dimension
        elif in_string.startswith("T:"):
            data = in_string[2:].split(',')
            try: 
                target_code = int(data[0].strip())
                target_desc = data[1].strip()
                dim_target_tuples.append((target_code, target_desc))
            except Exception as e:
                print("Error processing date:", e)

        # nationality dimension
        elif in_string.startswith("N:"):
            data = in_string[2:].split(',')
            try: 
                nationality_id = int(data[0].strip())
                nationality = data[1].strip()
                dim_nationality_tuples.append((nationality_id, nationality))
            except Exception as e:
                print("Error processing date:", e)

        # weapon dimension
        elif in_string.startswith("W:"):
            data = in_string[2:].split(',')
            try: 
                weapon_code = data[0].strip()
                weapon_desc = data[1].strip()
                dim_weapon_type_tuples.append((weapon_code, weapon_desc))
            except Exception as e:
                print("Error processing date:", e)

        # attack dimension
        elif in_string.startswith("A:"):
            data = in_string[2:].split(',')
            try: 
                attack_code = int(data[0].strip())
                attack_desc = data[1].strip()
                dim_attack_type_tuples.append((attack_code, attack_desc))
            except Exception as e:
                print("Error processing date:", e)

        # fact table
        elif in_string.startswith("F:"):
            data = in_string[2:].split(',')
            try: 
                event_id = data[0].strip()
                year = int(data[1].strip())
                month = int(data[2].strip())
                day = int(data[3].strip())

                try:
                    date = datetime.date(year, month, day)
                except ValueError:
                    date = datetime.date(2100, 1, 1)


                latitude = float(data[4].strip())
                longitude = float(data[5].strip())
                target_code = int(data[6].strip())
                victim_nationality_id = int(data[7].strip())
                weapon_code = int(data[8].strip())
                attack_code = int(data[9].strip())
                suicide = int(data[10].strip())
                success = int(data[11].strip())
                fatalities = int(data[12].strip())
                wounded = int(data[13].strip())
                ransom_demanded = int(data[14].strip())
                ransom_paid = int(data[15].strip())
                group_name = data[16].strip()
                motive = data[17].strip()

                fact_terror_event_tuples.append((event_id, date, latitude, longitude, target_code, victim_nationality_id, weapon_code, attack_code, suicide, success, fatalities, wounded, ransom_demanded, ransom_paid, group_name, motive))
            except Exception as e:
                print("Error processing date:", e)
    
if __name__ == '__main__':
    while True:
        dw_consumer()
    