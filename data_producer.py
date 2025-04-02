#!/usr/bin/env python3
from kafka import KafkaProducer
from time import sleep
import pandas as pd

def producer_f(topic,broker_addr):

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
        df = df.loc[(df["iyear"] >= 2015) & (df["iyear"] <= 2019)]
        
        df['nwound'] = df['nwound'].fillna(0).astype(int)
        df['nkill'] = df['nkill'].fillna(0).astype(int)
        df['natlty1'] = df['natlty1'].fillna(0).astype(int)
        df['ransom'] = df['ransom'].fillna(0).astype(int)
        df['ransomamt'] = df['ransomamt'].fillna(0).clip(lower=0).astype(int)
        df['ransompaid'] = df['ransompaid'].fillna(0).clip(lower=0).astype(int)
        df['latitude'] = df['latitude'].fillna(0).astype(float)
        df['longitude'] = df['longitude'].fillna(0).astype(float)



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

data_pipe = 'Data'
broker_addr = '127.0.0.1:29092'

producer_f(data_pipe, broker_addr)