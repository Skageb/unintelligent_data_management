#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error

def prepare_odb():
    # Connect to MySQL database
    conn = None
    create_db = " CREATE DATABASE IF NOT EXISTS odb"
    use_db = "use odb"
   
    create_table = "CREATE TABLE IF NOT EXISTS terrorism (eventid VARCHAR(20) NOT NULL PRIMARY KEY, year YEAR, month INT, day INT, country INT, country_txt VARCHAR(100), region INT, region_txt VARCHAR(100), city VARCHAR(100), latitude DOUBLE, longitude DOUBLE, success INT, suicide INT, attacktype INT, attacktype_txt VARCHAR(100), target_type INT, target_type_txt VARCHAR(100), victim_nat INT, victim_nat_txt VARCHAR(100), attacker_group VARCHAR(300), motive TEXT, weapon_type VARCHAR(20), weapon_type_txt VARCHAR(100), fatalities INT, wounded INT, ransom INT, ransom_demanded INT, ransom_paid INT)"        

    try:  
        conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=13306, 
                                  user='deuser',
                                  password='depassword')
        if conn.is_connected():
                print('Connected to MySQL database')
        
        cursor = conn.cursor()
        cursor.execute(create_db)
        cursor.execute(use_db)
        cursor.execute(create_table)

        cursor.execute("TRUNCATE TABLE terrorism")
        
        conn.commit()

        print('ODB is prepared')
        
            
    except Error as e:
        print(e)
        
    finally:
        if conn is not None and conn.is_connected():
            cursor.close()
            conn.close()
            
if __name__ == '__main__':
    prepare_odb()
    