#!/usr/bin/env python3
from kafka import KafkaProducer
from time import sleep
import pandas as pd

def producer_f(topic,broker_addr):

    producer = KafkaProducer(bootstrap_servers=broker_addr,api_version=(2,0,2))

    
    filename = "gtd.csv"
    
    try:
        df = pd.read_csv(filename,usecols=["eventid","iyear","imonth","iday", "nkill"])
        df = df[15:30]
        df['nkill'] = df['nkill'].fillna(0)

    except FileNotFoundError:
        print('File not found')
        return
    except ValueError:
        print(f'Missing columns: \n {ValueError}')
        return

    count = 0
    total_rows = len(df)
    index = 0

    while index < total_rows:
        count += 1
        row = df.iloc[index]
        line = ",".join(map(str,row.values))
        producer.send(topic,line.encode())
        
        sleep(1)

        if not line:
            break
        print("\nProduced input tuple {}: {}".format(count-1, line))

        index +=1

    producer.flush()
    print("\nDone with producing data to topic {}.".format(topic))

data_pipe = 'Data'
broker_addr = '127.0.0.1:29092'

producer_f(data_pipe, broker_addr)

