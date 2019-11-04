import psycopg2
from psycopg2 import Error
import time 
import requests
from PIL import Image 
import io
import cv2
import os
import numpy as np
import databaseMain as DB
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
		cursor.execute("SELECT 'public.rectable'::regclass")
	except:
		connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
		cursor = connection.cursor()
		cursor.execute("""CREATE TABLE rectable(id INT, worker TEXT, datetime TEXT, image TEXT)""")
		connection.commit()
	finally:
		cursor.close()
		connection.close()
		log_database_connections("dbRecognition.checkTable")

def insertData(deviceId, workerPK, currTime, frame):
	checkTable()
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	try:
		if workerPK == None:
			imageUrl = "/home/pi/koraupdate/imageDataSet/"'unknown_'+str(currTime.strftime("%Y_%m_%d_%H_%M_%S"))+".jpg"
		else:
			imageUrl = "/home/pi/koraupdate/imageDataSet/"+workerPK+'_'+str(currTime.strftime("%Y_%m_%d_%H_%M_%S"))+".jpg"
		cv2.imwrite(imageUrl, frame) 
		connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
		cursor = connection.cursor()
		postgres_insert_query = """ INSERT INTO rectable (id, worker, datetime, image) VALUES (%s,%s,%s,%s)"""
		
		record_to_insert = (deviceId, workerPK, currTime, imageUrl)
		cursor.execute(postgres_insert_query, record_to_insert)
		connection.commit()
		log_database_changes("Record inserted successfully into rectable")
	
	except Exception as e :
		log_exception(e, "dbRecognition.insertData")
	finally:
		if(connection):
			cursor.close()
			connection.close()
			log_database_connections("dbRecognition.insertData")

def sendData(auth_token, header, device_idn):
	checkTable()
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	cursor.execute("SELECT * from rectable")
	rows = cursor.fetchall()
	print(rows)
	for row in rows:
		print(row)
		try:
			#print(row)
			worker = row[1]
			datetime = str(row[2])
			img = row[3]
			files = {'photo': open(img, 'rb')}
			#print(type(files['photo']))
			r = requests.post("https://www.kora.work/api/checks/",
					headers=header,
					files=files,
					data={'device':device_idn,
						'worker': worker,
						'datetime': datetime},
						timeout=10)
			if(r.status_code == 200):
				print(r.text)
				if os.path.exists(img):
					os.remove(img)
					log_database_changes("Image successfully deleted from imageDataSet")
				else:
					print("The file does not exist")
				cursor.execute("DELETE FROM rectable WHERE datetime = '{}'".format(row[2]))
				connection.commit()
				log_database_changes("Record sent and deleted successfully from rectable")
		except Exception as e:
			print("Error Rec")
			log_exception(e, "dbRecognition.sendData")
	cursor.close()
	connection.close()
	log_database_connections("dbRecognition.sendData")
