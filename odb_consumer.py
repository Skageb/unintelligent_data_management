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
#import json
from time import sleep

def odb_consumer():
    # Connect to MySQL database
    conn = None
    query = "INSERT INTO terrorism(eventid, year, month, day, fatalities) " \
            "VALUES(%s, %s,%s,%s,%s)"
    
    consumer = KafkaConsumer('Data',bootstrap_servers='127.0.0.1:29092',api_version=(2,0,2))
    producer = KafkaProducer(bootstrap_servers='127.0.0.1:29092')
                             
    #tuples = [('jones','loc1','prod1', 10),('smith','loc1','prod1', 20),('jones','loc1','prod1', 10)]  
    
    print('\nWaiting for INPUT TUPLES, Ctr/Z to stop ...')
    
    tuples = [] 
    z = 0

    for message in consumer:
        in_string = message.value.decode()
        in_tuple = in_string.strip('"').split(',')
        print ('\nInput Tuple Received: {}'.format(in_tuple))
        
        sleep(1)

        eventID = in_tuple[0]
        year = in_tuple[1]
        month = in_tuple[2]
        day = in_tuple[3]
        fatalities = in_tuple[4]

        tuples.append((eventID,year,month,day,fatalities))
        
        z = z+1
        
        if z == 15:
          break
     
    try:  
        conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=13306, 
                                  database = 'odb',
                                  user='deuser',
                                  password='depassword')
        if conn.is_connected():
                print('\nConnected to destination ODB MySQL database')
        
        cursor = conn.cursor()
        
        for tuple in tuples:
            cursor.execute(query,tuple)
            
        conn.commit()
        
        cursor.execute("SELECT count(*) FROM terrorism")
        res = cursor.fetchone()
    
        print('ODB is populated: {} new tuples are inserted'.format(len(tuples)))
        print('                  {} total tuples are inserted'.format(res[0]))    
        
        sleep(2)
        
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
    