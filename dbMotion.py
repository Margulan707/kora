import psycopg2
from psycopg2 import Error
import time 
from datetime import datetime
import databaseMain as DB
import requests
from logfile import *

log_init()

DB.databaseInit()

def checkTable():
	try:
		connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
		cursor = connection.cursor()
		cursor.execute("SELECT 'public.motiontable'::regclass")
	except:
		connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
		cursor = connection.cursor()
		cursor.execute("""CREATE TABLE motiontable(id INT, startTime TEXT, finishTime TEXT)""")
		connection.commit()
	finally:
		cursor.close()
		connection.close()
		log_database_connections("dbMotion.checkTable")
def insertData(deviceId, currentTime, finishTime):
	checkTable()
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	try:
			record_to_insert = (deviceId, currentTime, finishTime)
			cursor.execute("SELECT * from motiontable")
			rows = cursor.fetchall()
			if(len(rows)):
				sTime = rows[len(rows)-1][1]
				fTime = rows[len(rows)-1][2]
				#print(fTime)
				time1 = datetime.strptime(fTime, '%Y-%m-%d %H:%M:%S.%f')
				#print(type(time1))
				elapsedTime = (currentTime - time1).total_seconds()
				#print(elapsedTime)
				if elapsedTime < 300:
					query = "UPDATE motiontable SET finishtime = %s WHERE starttime = %s"
					record_to_update = (finishTime, sTime)
					cursor.execute(query, record_to_update)
					connection.commit()
					log_database_changes("Record updated successfully into motiontable")
				else:
					postgres_insert_query = """ INSERT INTO motiontable (id, startTime, finishTime) VALUES (%s,%s,%s)"""
					cursor.execute(postgres_insert_query, record_to_insert)
					connection.commit()
					log_database_changes("Record inserted successfully into motiontable")
			else:
				postgres_insert_query = """ INSERT INTO motiontable (id, startTime, finishTime) VALUES (%s,%s,%s)"""
				cursor.execute(postgres_insert_query, record_to_insert)
				connection.commit()
				log_database_changes("Record inserted successfully into motiontable")						
	except Exception as e :
		log_exception(e)

	finally:
		if(connection):
			cursor.close()
			connection.close()
			log_database_connections("dbMotion.insertData")

def sendData(auth_token, header, device_idn):
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	cursor.execute("SELECT * from motiontable")
	rows = cursor.fetchall()
	for row in rows:
		try:
			r = requests.post("https://www.kora.work/api/motions/",
				headers=header,
				data={'device':device_idn,
					'starttime': str(row[1]),
					'finishtime': str(row[2])},
					timeout=10)
			if(r.status_code == 200):
				cursor.execute("DELETE FROM motiontable WHERE starttime = '{}'".format(row[1]))
				connection.commit()
				log_database_changes("Record sent and deleted successfully from motiontable")
		except Exception as e:
			log_exception(e, "dbMotion.sendData")
	cursor.close()
	connection.close()
	log_database_connections("dbMotion.sendData")
