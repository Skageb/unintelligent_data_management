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
    create_db = " CREATE DATABASE IF NOT EXISTS dw"
    use_db = "use dw"

    # dimentional tables
    create_table1 = "CREATE TABLE IF NOT EXISTS dim_date (date_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, month INT, day INT, date_string DATE)"
    create_table2 = "CREATE TABLE IF NOT EXISTS dim_location (location_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, country_code INT, country_txt VARCHAR(100), region_code INT, region_name VARCHAR(100), city VARCHAR(100))"
    create_table3 = "CREATE TABLE IF NOT EXISTS dim_target (target_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target_code INT, target_desc VARCHAR(100), nationality_id INT, nationality VARCHAR(100))"
    create_table4 = "CREATE TABLE IF NOT EXISTS dim_perpetrator (perpetrator_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, group_name VARCHAR(300), motive TEXT)"
    create_table5 = "CREATE TABLE IF NOT EXISTS dim_weapon_type (weapon_type_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, weapon_code INT, weapon_desc VARCHAR(100))"
    create_table6 = "CREATE TABLE IF NOT EXISTS dim_attack_type (attack_type_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, attack_code INT, attack_desc VARCHAR(300))"

    # fact table
    create_table7 = "CREATE TABLE IF NOT EXISTS fact_terror_event (event_id VARCHAR(20) PRIMARY KEY, date_id INT NOT NULL, location_id INT NOT NULL, attack_type_id INT NOT NULL, \
        target_id INT NOT NULL, perpetrator_id INT NOT NULL, weapon_type_id INT NOT NULL, success INT, suicide INT, fatalities INT, wounded INT, ransom_demanded INT, ransom_paid INT, \
        FOREIGN KEY (date_id) REFERENCES dim_date(date_id), FOREIGN KEY (location_id) REFERENCES dim_location(location_id), FOREIGN KEY (attack_type_id) REFERENCES dim_attack_type(attack_type_id), \
        FOREIGN KEY (target_id) REFERENCES dim_target(target_id), FOREIGN KEY (perpetrator_id) REFERENCES dim_perpetrator(perpetrator_id), FOREIGN KEY (weapon_type_id) REFERENCES dim_weapon_type(weapon_type_id))"

    # summary table

    #create_table1 = "CREATE TABLE IF NOT EXISTS fatalities (fatalitiesId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, fatalities INT)"          
    #create_table2 = "CREATE TABLE IF NOT EXISTS ransom_by_country (ransomId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, country INT, country_txt VARCHAR(100), ransom_demanded INT, ransom_paid INT)"
    #create_table3 = "CREATE TABLE IF NOT EXISTS terror_in_norway (terrorId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, city VARCHAR(100), fatalities INT, wounded INT, success INT, suicide INT, attacker_group VARCHAR(300), target_type VARCHAR(100), weapon_type VARCHAR(100), motive TEXT)"
    #create_table4 = "CREATE TABLE IF NOT EXISTS weapon_type (weapId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, weapon_type INT, weapon_type_desc VARCHAR(100), fatalities INT, wounded INT, occurences INT)"

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
        cursor.execute(create_table5)
        cursor.execute(create_table6)
        cursor.execute(create_table7)

        
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
    