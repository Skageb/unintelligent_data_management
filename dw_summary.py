#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error

def dw_summary():

    # fatalities
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

    # ransom
    dw_aggregate_query2= """
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

    # terror by country
    dw_aggregate_query3 = """
        SELECT year,
            country_code AS country,
            country_txt,
            SUM(number_of_attacks) OVER (PARTITION BY country_code, country_txt ORDER BY year) AS cumulative_attacks
        FROM (
            SELECT YEAR(f.date) AS year,
                l.country_code,
                l.country_txt,
                COUNT(*) AS number_of_attacks
            FROM fact_terror_event f
            JOIN dim_location l ON f.latitude = l.latitude AND f.longitude = l.longitude
            GROUP BY YEAR(f.date), l.country_code, l.country_txt
        ) AS yearly
        ORDER BY country_code, year
    """

    # weapon type
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
    insert_fatalities = "INSERT IGNORE INTO fatalities(year,fatalities) VALUES(%s,%s)"
    insert_ransom = "INSERT IGNORE INTO ransom_by_country(year, country, country_txt, ransom_demanded, ransom_paid) VALUES(%s,%s,%s,%s,%s)"
    insert_country = "INSERT IGNORE INTO terror_by_country (year, country, country_txt, number_of_attacks) VALUES (%s, %s, %s, %s)"
    insert_weapon = "INSERT IGNORE INTO weapon_type(year, weapon_type, weapon_type_desc, fatalities, wounded, occurences) VALUES(%s,%s,%s,%s,%s,%s)"

    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=23306,
            database='dw',
            user='deuser',
            password='depassword'
        )
        if conn.is_connected():
            print("Connected to DW MySQL")

        cursor = conn.cursor()


        # fatalities
        cursor.execute(dw_aggregate_query1)
        rows = cursor.fetchall()
        cursor.executemany(insert_fatalities, [(int(row[0]), int(row[1])) for row in rows])

        # ransom
        cursor.execute(dw_aggregate_query2)
        rows = cursor.fetchall()
        cursor.executemany(insert_ransom, rows)

        # norway
        cursor.execute(dw_aggregate_query3)
        rows = cursor.fetchall()
        cursor.executemany(insert_country, rows)

        # weapon type
        cursor.execute(dw_aggregate_query4)
        rows = cursor.fetchall()
        cursor.executemany(insert_weapon, rows)

        conn.commit()
        print("\nDW summary tables updated")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    dw_summary()
