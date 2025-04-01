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

def dw_consumer():
    # Connect to MySQL database
    dw_conn = None

    dw_load_query1 = "INSERT INTO dim_date(year, month, day) " \
                      "VALUES(%s,%s,%s)"
    
    dw_load_query2 = "INSERT INTO dim_location(country_code, country_txt, region_code, region_name, city) " \
                      "VALUES(%s,%s,%s,%s,%s)"
    
    dw_load_query3 = "INSERT INTO dim_target(target_code, target_desc, nationality_id, nationality) " \
                      "VALUES(%s,%s,%s,%s)"
    
    dw_load_query4 = "INSERT INTO dim_perpetrator(group_name, motive) " \
                      "VALUES(%s,%s)"
    
    dw_load_query5 = "INSERT INTO dim_weapon_type(weapon_code, weapon_desc) " \
                      "VALUES(%s,%s)"
    
    dw_load_query6 = "INSERT INTO dim_attack_type(attack_code, attack_desc) " \
                      "VALUES(%s,%s)"
    
    # dw_load_query7 = "INSERT INTO fact_terror_event(event_id, date_id, location_id, attack_type_id, target_id, perpetrator_id, " \
    # "weapon_type_id, success, suicide, fatalities, wounded, ransom_demanded, ransom_paid) " \
    #                   "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    
    
    
    # dw_load_query1 = "INSERT INTO fatalities(year,fatalities) " \
    #                  "VALUES(%s,%s)"
    
    # dw_load_query2 = "INSERT INTO ransom_by_country(year, country, country_txt, ransom_demanded, ransom_paid) " \
    #                  "VALUES(%s,%s,%s,%s,%s)"
    
    # dw_load_query3 = "INSERT INTO terror_in_norway(year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive) " \
    #                  "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    
    # dw_load_query4 = "INSERT INTO weapon_type(year, weapon_type, weapon_type_desc, fatalities, wounded, occurences) " \
    #                  "VALUES(%s,%s,%s,%s,%s,%s)"
    
    
    consumer = KafkaConsumer('AggrData',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
    
    print('\nWaiting for AGGREGATED TUPLES, Ctr/Z to stop ...')
    
    dim_date_tuples = []
    dim_location_tuples = []
    dim_target_tuples = []
    dim_perpetrator_tuples = []
    dim_weapon_type_tuples = []
    dim_attack_type_tuples = []

    #fact_terror_event_tuples = []

    # fatalities_tuples = [] 
    # ransom_tuples = []
    # norway_tuples = []
    # weapon_tuples = []

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
            
                dw_cursor.executemany(dw_load_query1, dim_date_tuples)
                dw_cursor.executemany(dw_load_query2, dim_location_tuples)
                dw_cursor.executemany(dw_load_query3, dim_target_tuples)
                dw_cursor.executemany(dw_load_query4, dim_perpetrator_tuples)
                dw_cursor.executemany(dw_load_query5, dim_weapon_type_tuples)
                dw_cursor.executemany(dw_load_query6, dim_attack_type_tuples)

                #dw_cursor.executemany(dw_load_query7, fact_terror_event_tuples)



                # dw_cursor.executemany(dw_load_query1, fatalities_tuples)
                # dw_cursor.executemany(dw_load_query2, ransom_tuples)
                # dw_cursor.executemany(dw_load_query3, norway_tuples)
                # dw_cursor.executemany(dw_load_query4, weapon_tuples)
                
                dw_conn.commit()

                dw_cursor.execute("SELECT count(*) FROM dim_date")
                date_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_location")
                location_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_target")
                target_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_perpetrator")
                perpetrator_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_weapon_type")
                weapon_count = dw_cursor.fetchone()[0]

                dw_cursor.execute("SELECT count(*) FROM dim_attack_type")
                attack_count = dw_cursor.fetchone()[0]

                # dw_cursor.execute("SELECT count(*) FROM fact_terror_event")
                # fact_count = dw_cursor.fetchone()[0]
                
                # dw_cursor.execute("SELECT count(*) FROM fatalities")
                # fatalities_count = dw_cursor.fetchone()[0]

                # dw_cursor.execute("SELECT count(*) FROM ransom_by_country")
                # ransom_count = dw_cursor.fetchone()[0]

                # dw_cursor.execute("SELECT count(*) FROM terror_in_norway")
                # norway_count = dw_cursor.fetchone()[0]

                # dw_cursor.execute("SELECT count(*) FROM weapon_type")
                # weapon_count = dw_cursor.fetchone()[0]

                # print('DW is loaded: {} total fatalities records inserted'.format(fatalities_count))
                # print('              {} total ransom records are inserted'.format(ransom_count))
                # print('              {} total norway records are inserted'.format(norway_count))
                # print('              {} total weapon records are inserted'.format(weapon_count))

                    
            except Error as e:
                print(e)
                
            finally:
                if dw_conn is not None and dw_conn.is_connected():
                    dw_cursor.close()
                    dw_conn.close()
            break

        # date dimension
        if in_string.startswith("D:"):
            data = in_string[2:].split(',')
            try: 
                year = int(data[0].strip())
                month = int(data[1].strip())
                day = int(data[2].strip())
                dim_date_tuples.append((year, month, day))
            except Exception as e:
                print("Error processing date:", e)

        # location dimension
        elif in_string.startswith("L:"):
            data = in_string[2:].split(',')
            try: 
                country_code = int(data[0].strip())
                country_txt = data[1].strip()
                region_code = int(data[2].strip())
                region_name = data[3].strip()
                city = data[4].strip()
                dim_location_tuples.append((country_code, country_txt, region_code, region_name, city))
            except Exception as e:
                print("Error processing date:", e)

        # target dimension
        elif in_string.startswith("T:"):
            data = in_string[2:].split(',')
            try: 
                target_code = int(data[0].strip())
                target_desc = data[1].strip()
                nationality_id = int(data[2].strip())
                nationality = data[3].strip()
                dim_target_tuples.append((target_code, target_desc, nationality_id, nationality))
            except Exception as e:
                print("Error processing date:", e)

        # perpetrator dimension
        elif in_string.startswith("P:"):
            data = in_string[2:].split(',')
            try: 
                group_name = data[0].strip()
                motive = data[1].strip()
                dim_perpetrator_tuples.append((group_name, motive))
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

        # # fact terror event
        # elif in_string.startswith("F:"):
        #     data = in_string[2:].split(',')
        #     try: 
        #         event_id = data[0].strip()
        #         date_id = int(data[1].strip())
        #         location_id = int(data[2].strip())
        #         attack_type_id = int(data[3].strip())
        #         target_id = int(data[4].strip())
        #         perpetrator_id = int(data[5].strip())
        #         weapon_type_id = int(data[6].strip())
        #         success = int(data[7].strip())
        #         suicide = int(data[8].strip())
        #         fatalities = int(data[9].strip())
        #         wounded = int(data[10].strip())
        #         ransom_demanded = int(data[11].strip())
        #         ransom_paid = int(data[12].strip())

        #         fact_terror_event_tuples.append((
        #             event_id, date_id, location_id, attack_type_id, target_id,
        #             perpetrator_id, weapon_type_id, success, suicide, fatalities,
        #             wounded, ransom_demanded, ransom_paid
        #         ))
        #     except Exception as e:
        #         print("Error processing fact tuple:", e)



        # if in_string.startswith("F:"):
        #     data = in_string[2:].split(',')
        #     try: 
        #         year = int(data[0].strip())
        #         fatalities = int(data[1].strip())
        #         fatalities_tuples.append((year, fatalities))
        #         print("\nFatalities Tuple Received: ({}, {})".format(year, fatalities))
        #     except Exception as e:
        #         print("Error processing fatalities data:", e)

        # elif in_string.startswith("R:"):
        #     data = in_string[2:].split(',')
        #     try:
        #         year = data[0].strip()
        #         country = data[1].strip()
        #         country_txt = data[2].strip()
        #         total_ransom_demanded = int(data[3].strip())
        #         total_ransom_paid = int(data[4].strip())
        #         ransom_tuples.append((year, country, country_txt, total_ransom_demanded, total_ransom_paid))
        #         print("\nRansom Tuple Received: ({}, {}, {}, {}, {})".format(year, country, country_txt, total_ransom_demanded, total_ransom_paid))
        #     except Exception as e:
        #         print("Error processing ransom data:", e)
        # elif in_string.startswith("N:"):
        #     data = in_string[2:].split(',')
        #     try:
        #         year = data[0].strip()
        #         city = data[1].strip()
        #         fatalities = int(data[2].strip())
        #         wounded = int(data[3].strip())
        #         success = int(data[4].strip())
        #         suicide = int(data[5].strip())
        #         attacker_group = data[6].strip()
        #         target_type = data[7].strip()
        #         weapon_type = data[8].strip()
        #         motive = data[9].strip()
        #         norway_tuples.append((year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive))
        #         print("\nNorway Tuple Received: ({}, {}, {}, {}, {}, {}, {}, {}, {})".format(year, city, fatalities, wounded, success, suicide, attacker_group, target_type, weapon_type, motive))
        #     except Exception as e:
        #         print("Error processing ransom data:", e)
        # elif in_string.startswith("W:"):
        #     data = in_string[2:].split(',')
        #     try:
        #         year = data[0].strip()
        #         weapon_type = int(data[1].strip())
        #         weapon_type_txt = data[2].strip()
        #         fatalities = int(data[3].strip())
        #         wounded = int(data[4].strip())
        #         eventid = int(data[5].strip())
        #         weapon_tuples.append((year, weapon_type, weapon_type_txt, fatalities, wounded,eventid))
        #         print("\nWeapon Tuple Received: ({}, {}, {}, {}, {}, {})".format(year, weapon_type, weapon_type_txt, fatalities, wounded,eventid))
        #     except Exception as e:
        #         print("Error processing ransom data:", e)
    
if __name__ == '__main__':
    while True:
        dw_consumer()
    