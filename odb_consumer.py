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

from kafka import KafkaConsumer, KafkaProducer

def odb_consumer():
    # Connect to MySQL database
    conn = None
    query = "INSERT INTO terrorism(eventid, year, month, day, country, country_txt, region, region_txt, city, success, suicide, attacktype, attacktype_txt, target_type, target_type_txt, victim_nat, victim_nat_txt, attacker_group, motive, weapon_type, weapon_type_txt, fatalities, wounded, ransom, ransom_demanded, ransom_paid) "\
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    
    consumer = KafkaConsumer('Data',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
    producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')
                             
    #tuples = [('jones','loc1','prod1', 10),('smith','loc1','prod1', 20),('jones','loc1','prod1', 10)]  
    
    print('\nWaiting for INPUT TUPLES, Ctr/Z to stop ...')
    
    tuples = [] 
    total_inserted = 0
    batch_size = 1000

    for message in consumer:
        in_string = message.value.decode()

        if in_string == "DONE":
            print("\nProducer has finished sending data. Processing remaining tuples...")
            break

        in_tuple = in_string.strip('"').split(',')
                
        eventID = in_tuple[0]
        year = in_tuple[1]
        month = in_tuple[2]
        day = in_tuple[3]
        country = in_tuple[4]
        country_txt = in_tuple[5]
        region = in_tuple[6]
        region_txt = in_tuple[7]
        city = in_tuple[8]
        success = in_tuple[9]
        suicide = in_tuple[10]
        attacktype = in_tuple[11]
        attacktype_txt = in_tuple[12]
        target_type = in_tuple[13]
        target_type_txt = in_tuple[14]
        victim_nat = in_tuple[15]
        victim_nat_txt = in_tuple[16]
        attacker_group = in_tuple[17]
        motive = in_tuple[18]
        weapon_type = in_tuple[19]
        weapon_type_txt = in_tuple[20]
        fatalities = in_tuple[21]
        wounded = in_tuple[22]
        ransom = in_tuple[23]
        ransom_demanded = in_tuple[24]
        ransom_paid = in_tuple[25]

        tuples.append((
            eventID, year, month, day,
            country, country_txt,
            region, region_txt,
            city, success,
            suicide, attacktype,
            attacktype_txt,
            target_type, target_type_txt,
            victim_nat, victim_nat_txt,
            attacker_group, motive,
            weapon_type, weapon_type_txt,
            fatalities, wounded,
            ransom, ransom_demanded, ransom_paid
        ))

        if len(tuples) == batch_size:
            try:
                if conn is None or not conn.is_connected():
                    conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=13306, 
                                  database = 'odb',
                                  user='deuser',
                                  password='depassword')
                cursor = conn.cursor()
                cursor.executemany(query, tuples)
                conn.commit()
                total_inserted += len(tuples)
                print(f'Inserted {total_inserted} rows so far...')
                tuples.clear()
            except Error as e:
                print(f'Batch insert failed: {e}')
                break
        
    if tuples:
        try:
            if conn is None or not conn.is_connected():
                conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                port=13306, 
                                database = 'odb',
                                user='deuser',
                                password='depassword')
            cursor = conn.cursor()
            cursor.executemany(query, tuples)
            conn.commit()
            total_inserted += len(tuples)
            print(f'Final batch inserted. Total rows inserted: {total_inserted}')
        except Error as e:
            print(f'Final insert failed: {e}')

    try:  
        cursor.execute("SELECT count(*) FROM terrorism")
        res = cursor.fetchone()
    
        m = 'odb update event'   
        producer.send('odb-update-stream', m.encode())
        print('\nODB UPDATE EVENT SENT TO ODB UPDATE STREAM')
        producer.flush()
        
            
    except Error as e:
        print(e)
        
    finally:
        if conn is not None and conn.is_connected():
            cursor.close()
            conn.close()
            
if __name__ == '__main__':
    odb_consumer()
    