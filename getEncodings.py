import requests
import time
import json
import numpy as np
import psycopg2
from logfile import *

log_init()

def checkTable():
    try:
        connection = psycopg2.connect(
            user = "postgres",
            password = "1231",
            host = "127.0.0.1",
            port = "5432",
            database = "raspberry")
        cursor = connection.cursor()
        cursor.execute("SELECT 'public.encodingstable'::regclass")
    except:
        connection = psycopg2.connect(
            user = "postgres",
            password = "1231",
            host = "127.0.0.1",
            port = "5432",
            database = "raspberry")
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE encodingstable(encoding NUMERIC[], pk TEXT)""")
        connection.commit()
    finally:
        cursor.close()
        connection.close()
        log_database_connections("getEncodings.checkTable")
            
def refreshEncodings(auth_token, header, device_idn):
    checkTable()
    try:
        r = requests.get("https://www.kora.work/api/devices/"+device_idn+"/encodings/", headers=header, timeout=10)
        
        if r.status_code == 200:
            json_data = json.loads(r.text)
            connection = psycopg2.connect(
                user = "postgres",
                password = "1231",
                host = "127.0.0.1",
                port = "5432",
                database = "raspberry")
            cursor = connection.cursor()
            cursor.execute("DROP TABLE encodingstable")
            connection.commit()
            checkTable()
            for worker in json_data:
                temp = worker['faceEncodings'].split("[")[2].split("]")[0]
                encoding = np.fromstring(temp, dtype=float, sep=',')
                encoding = encoding.tolist()
                pk = worker['pk']
                postgres_insert_query = """INSERT INTO encodingstable(encoding, pk) VALUES (%s,%s)"""
                record_to_insert = (encoding, pk)
                cursor.execute(postgres_insert_query, record_to_insert)
                connection.commit()
                log_database_changes("Record inserted successfully into encodingstable")
            cursor.close()
            connection.close()
            log_database_connections("getEncodings.refreshEncodings")
    except Exception as e:
        log_exception(e, "refreshEncodings")
