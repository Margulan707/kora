import psycopg2
from psycopg2 import Error
from psycopg2 import sql
import time 
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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
		cursor.execute("SELECT 'public.activitytable'::regclass")
	except:
		connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
		cursor = connection.cursor()
		cursor.execute("CREATE TABLE activitytable(id INT, startTime TEXT, finishTime TEXT)")
		connection.commit()
	finally:
		cursor.close()
		connection.close()
		log_database_connections("dbActivity.checkTable")

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
		cursor.execute("SELECT * from activitytable")
		rows = cursor.fetchall()
		if(len(rows)):
			sTime = rows[len(rows)-1][1]
			fTime = rows[len(rows)-1][2]
			#print(fTime)
			currentTime = datetime.strptime(currentTime, '%Y-%m-%d %H:%M:%S.%f')
			time1 = datetime.strptime(fTime, '%Y-%m-%d %H:%M:%S.%f')
			#print(type(time1))
			elapsedTime = (currentTime - time1).total_seconds()
			#print(elapsedTime)
			if elapsedTime < 300 and (currentTime.day == time1.day):
				query = "UPDATE activitytable SET finishtime = %s WHERE starttime = %s"
				record_to_update = (finishTime, sTime)
				cursor.execute(query, record_to_update)
				connection.commit()
				log_database_changes("Record updated successfully into activitytable")
			else:
				postgres_insert_query = """ INSERT INTO activitytable (id, startTime, finishTime) VALUES (%s,%s,%s)"""
				cursor.execute(postgres_insert_query, record_to_insert)
				connection.commit()
				log_database_changes("Record inserted successfully into activitytable")
		else:
			postgres_insert_query = """ INSERT INTO activitytable (id, startTime, finishTime) VALUES (%s,%s,%s)"""
			cursor.execute(postgres_insert_query, record_to_insert)
			connection.commit()
			log_database_changes("Record inserted successfully into activitytable")
	except Exception as e :
		log_exception(e, "dbActivity.insertData")

	finally:
		if(connection):
			cursor.close()
			connection.close()
			log_database_connections("dbActivity.insertData")

def sendData(auth_token, header, device_idn):
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	cursor.execute("SELECT * from activitytable")
	rows = cursor.fetchall()
	print(rows)
	for row in rows:
		print(row)
		try:
			r = requests.post("https://www.kora.work/api/status/devices/",
					headers=header,
					data={'device':device_idn,
						'starttime': str(row[1]),
						'finishtime': str(row[2])},
						timeout=10)
			if(r.status_code == 200):
				print(r.text)
				cursor.execute("DELETE FROM activitytable WHERE starttime = '{}'".format(row[1]))
				connection.commit()
				log_database_changes("Record sent and deleted successfully from activitytable")
		except Exception as e:
			print("Error Activity")
			log_exception(e, "dbActivity.sendData")
	cursor.close()
	connection.close()
	log_database_connections("dbActivity.sendData")
