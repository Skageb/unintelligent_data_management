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

    # dimension tables
    create_table1 = "CREATE TABLE IF NOT EXISTS dim_location (country_code INT, country_txt VARCHAR(100), region_code INT, region_name VARCHAR(100), city VARCHAR(100), latitude DOUBLE, longitude DOUBLE, PRIMARY KEY (latitude, longitude))"
    create_table2 = "CREATE TABLE IF NOT EXISTS dim_target (target_code INT NOT NULL PRIMARY KEY, target_desc VARCHAR(100))"
    create_table3 = "CREATE TABLE IF NOT EXISTS dim_nationality (victim_nationality_id INT NOT NULL PRIMARY KEY, victim_nationality_desc VARCHAR(100))"
    create_table4 = "CREATE TABLE IF NOT EXISTS dim_weapon_type (weapon_code VARCHAR(20) NOT NULL PRIMARY KEY, weapon_desc VARCHAR(100))"
    create_table5 = "CREATE TABLE IF NOT EXISTS dim_attack_type (attack_code INT NOT NULL PRIMARY KEY, attack_desc VARCHAR(300))"

    # fact table
    create_table6 = "CREATE TABLE IF NOT EXISTS fact_terror_event (event_id VARCHAR(20) PRIMARY KEY, date DATE, latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL, \
        target_code INT NOT NULL, victim_nationality_id INT NOT NULL, weapon_code VARCHAR(20) NOT NULL, attack_code INT NOT NULL, success INT, suicide INT, fatalities INT, wounded INT, ransom_demanded INT, ransom_paid INT, \
        group_name VARCHAR(300), motive TEXT, \
        FOREIGN KEY (latitude, longitude) REFERENCES dim_location(latitude, longitude), FOREIGN KEY (target_code) REFERENCES dim_target(target_code), \
        FOREIGN KEY (victim_nationality_id) REFERENCES dim_nationality(victim_nationality_id), FOREIGN KEY (weapon_code) REFERENCES dim_weapon_type(weapon_code), \
        FOREIGN KEY (attack_code) REFERENCES dim_attack_type(attack_code))"


    # summary tables

    create_table7 = "CREATE TABLE IF NOT EXISTS fatalities (fatalitiesId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, fatalities INT, UNIQUE KEY uniq_year_fatalities(year,fatalities))"          
    create_table8 = "CREATE TABLE IF NOT EXISTS ransom_by_country (ransomId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, country INT, country_txt VARCHAR(100), ransom_demanded INT, ransom_paid INT, UNIQUE KEY uniq_year_ransom(year,country))"
    create_table9 = "CREATE TABLE IF NOT EXISTS terror_in_norway (terrorId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, city VARCHAR(100), fatalities INT, wounded INT, success INT, suicide INT, attacker_group VARCHAR(300), target_type VARCHAR(100), weapon_type VARCHAR(100), motive TEXT, UNIQUE KEY uniq_norway_summary (year, city, fatalities, attacker_group, target_type, weapon_type))"
    create_table10 = "CREATE TABLE IF NOT EXISTS weapon_type (weapId INT NOT NULL AUTO_INCREMENT PRIMARY KEY, year YEAR, weapon_type INT, weapon_type_desc VARCHAR(100), fatalities INT, wounded INT, occurences INT, UNIQUE KEY uniq_year_weapon(year,weapon_type))"

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
        cursor.execute(create_table8)
        cursor.execute(create_table9)
        cursor.execute(create_table10)

        # resetting the database before preparing
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ['fact_terror_event', 'dim_location', 'dim_target', 'dim_nationality',
                      'dim_weapon_type', 'dim_attack_type', 'fatalities', 'ransom_by_country',
                      'terror_in_norway', 'weapon_type']:
            cursor.execute(f"TRUNCATE TABLE {table}")

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
    