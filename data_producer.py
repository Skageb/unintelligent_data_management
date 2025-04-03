#!/usr/bin/env python3
from kafka import KafkaProducer
from time import sleep
import pandas as pd
import sys

def producer_f(topic, broker_addr, start_year=2015, end_year=2019):

    producer = KafkaProducer(bootstrap_servers=broker_addr,api_version=(2,0,2))

    
    filename = "gtd.csv"


    try:
        df = pd.read_csv(filename, usecols = [
        "eventid", "iyear", "imonth", "iday", "country", "country_txt", "region", "region_txt",
        "city", "latitude", "longitude", "success", "suicide", "attacktype1", "attacktype1_txt", "targtype1",
        "targtype1_txt", "natlty1", "natlty1_txt", "gname", "motive", "weaptype1", "weaptype1_txt", "nkill", "nwound",
        "ransom", "ransomamt", "ransompaid"
    ]
)
        df = df.loc[(df["iyear"] >= start_year) & (df["iyear"] <= end_year)]
        
        df['nwound'] = df['nwound'].fillna(0).astype(int)
        df['nkill'] = df['nkill'].fillna(0).astype(int)
        df['natlty1'] = df['natlty1'].fillna(0).astype(int)
        df['ransom'] = df['ransom'].fillna(0).astype(int)
        df['ransomamt'] = df['ransomamt'].fillna(0).clip(lower=0).astype(int)
        df['ransompaid'] = df['ransompaid'].fillna(0).clip(lower=0).astype(int)
        df = df.dropna(subset=['latitude', 'longitude','iyear','imonth','iday'])
        df = df[(df['imonth'] >= 1) & (df['imonth'] <= 12)]
        df = df[(df['iday'] >= 1) & (df['iday'] <= 31)]



    except FileNotFoundError:
        print('File not found')
        return
    except ValueError as e:
        print(f'Error {e}')
        return

    count = 0
    total_rows = len(df)
    index = 0

    while index < total_rows:
        count += 1
        row = df.iloc[index]
        line = ",".join("" if v is None else str(v).replace(",", ";") for v in row.values)
        producer.send(topic,line.encode())
        
        if not line:
            break

        if index % 1000 == 0:
            print(f'Produced input number: {count-1}')

        index +=1

    producer.send(topic, b"DONE")
    producer.flush()
    print("\nDone with producing data to topic {}.".format(topic))

if __name__ == "__main__":
    data_pipe = 'Data'
    broker_addr = '127.0.0.1:29092'

    allowed_years = set(range(1970, 2021))
    args = sys.argv[1:]

    if len(args) == 0:
        start, end = 2015, 2019
    elif len(args) == 1:
        try:
            year = int(args[0])
            if year not in allowed_years:
                raise ValueError
            start = end = year
        except ValueError:
            print("Invalid year. Please provide a year between 1970 and 2020")
            sys.exit(1)
    elif len(args) == 2:
        try:
            start = int(args[0])
            end = int(args[1])
            if start not in allowed_years or end not in allowed_years:
                raise ValueError("Years must be between 1970 and 2020")
            if start > end:
                raise ValueError("Start year must be less than or equal to end year.")
        except ValueError as ve:
            print(f"Invalid input: {ve}")
            sys.exit(1)
    else:
        print("Usage: data_producer.py [start_year] [end_year]")
        sys.exit(1)

    producer_f(data_pipe, broker_addr, start_year=start, end_year=end)