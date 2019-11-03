import psycopg2
from psycopg2 import Error
from psycopg2 import sql
import time 
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from logfile import *

def databaseInit():
    try:
        connection = psycopg2.connect(
        user = "postgres",
        password = "1231",
        host = "127.0.0.1",
        port = "5432",
        database = "raspberry")
        cursor = connection.cursor()
    except:
        connection = psycopg2.connect(
            user="postgres", 
            host='127.0.0.1',
            password="1231")
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE {};".format("raspberry"))
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            log_database_connections("databaseMain.databaseInit")
