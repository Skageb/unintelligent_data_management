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

def prepare_dw():
    # Connect to MySQL database
    conn = None
    create_db = " CREATE DATABASE dw"
    use_db = "use dw"

    create_table1 = "CREATE TABLE fatalities (fatalitiesId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, fatalities INT)"          
    create_table2 = "CREATE TABLE ransom_by_country (ransomId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, country INT, country_txt VARCHAR(100), ransom_demanded INT, ransom_paid INT)"
    create_table3 = "CREATE TABLE terror_in_norway (terrorId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, city VARCHAR(100), fatalities INT, wounded INT, success INT, suicide INT, attacker_group VARCHAR(300), target_type VARCHAR(100), weapon_type VARCHAR(100), motive TEXT)"
    create_table4 = "CREATE TABLE weapon_type (weapon_type INT NOT NULL PRIMARY KEY, weapon_type_desc VARCHAR(100), fatalities INT, wounded INT, occurences INT)"

    try:  
        conn = mysql.connector.connect(host='127.0.0.1', # !!! make sure you use your VM IP here !!!
                                  port=23306, 
                                  user='deuser',
                                  password='depassword')
        if conn.is_connected():
                print('Connected to MySQL database')
        
        cursor = conn.cursor()
        cursor.execute(create_db)
        cursor.execute(use_db)
        cursor.execute(create_table1)
        cursor.execute(create_table2)
        cursor.execute(create_table3)
        cursor.execute(create_table4)
        
        conn.commit()

        print('DW is prepared')
        
            
    except Error as e:
        print(e)
        
    finally:
        if conn is not None and conn.is_connected():
            cursor.close()
            conn.close()
            
if __name__ == '__main__':
    prepare_dw()
    