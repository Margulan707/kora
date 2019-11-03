import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.output(21, GPIO.HIGH)
GPIO.output(12, GPIO.HIGH)
GPIO.output(16, GPIO.HIGH)
import picamera
import requests
import face_recognition
import cv2
import time
import json
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
import os
import io
import imutils
from threading import Timer, Thread
import subprocess
import base64
import psycopg2

import dbRecognition as dbR
import dbActivity as dbA
import dbMotion as dbM

_FINISH = False

known_face_encodings = []
known_face_pk = []
unknown_face_encodings = []
unknown_face_pk = []
sended_face_pk = []
sended_unknown = []
language = 'en'
firstFrame = None
counter_motion = 0
counter_motion_first = 0
counter_internet = 0
counter_live = 0
face_cascade = cv2.CascadeClassifier('/home/pi/koraupdater/kora/haarcascade_frontalface_default.xml')
frame = None
error_counter=0

def saveEncodings():
	connection = psycopg2.connect(
			user = "postgres",
			password = "1231",
			host = "127.0.0.1",
			port = "5432",
			database = "raspberry")
	cursor = connection.cursor()
	cursor.execute("SELECT * from encodingstable")
	rows = cursor.fetchall()
	for row in rows:
		encoding = []
		for num in row[0]:
			encoding.append(float(num))
		known_face_encodings.append(encoding)
		known_face_pk.append(row[1])

def refreshSendedList(delete_pk):
	global sended_face_pk
	sended_face_pk.remove(delete_pk)

def refreshUnknownList(encodings):
	unknown_face_encodings.remove(encodings)

def sendPK(name_index, frame, device_idn):
	global known_face_pk
	dbR.insertData(device_idn, known_face_pk[name_index], str(datetime.now()), frame)
	GPIO.output(12, GPIO.LOW)

def sendUnknown(name_index, frame, device_idn):
	dbR.insertData(device_idn, None, str(datetime.now()), frame)
	GPIO.output(21, GPIO.LOW)

def sendMovement(boolean, device_idn):
	dbM.insertData(device_idn, datetime.now(), datetime.now())

def sendActivity(device_idn):
	global _FINISH
	dbA.insertData(device_idn, datetime.now(), datetime.now())
	if not _FINISH:
		Timer(60, sendActivity, args=[device_idn]).start()



for i in range(5):
	GPIO.output(16, GPIO.HIGH)
	GPIO.output(21, GPIO.HIGH)
	GPIO.output(12, GPIO.HIGH)
	time.sleep(0.2)
	GPIO.output(12, GPIO.LOW)
	GPIO.output(16, GPIO.LOW)
	GPIO.output(21, GPIO.LOW)
	time.sleep(0.2)

def startRecognition(device_idn):
	counter_motion = 0
	counter_motion_first = 0
	movement_time = datetime.now()
	camera = picamera.PiCamera()
	camera.resolution = (960, 720)
	frame = np.empty((720,960,3),dtype=np.uint8)
	while True:
		try:
			camera.capture(frame, format="rgb", use_video_port=True)
			#
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			faces = face_cascade.detectMultiScale(gray, 1.3, 5)
			faces = list(faces)
			#if face is found
			if faces:
				GPIO.output(16, GPIO.HIGH)
				for (x,y,w,h) in faces:
					face_loc = list([tuple(np.array([y, x+w, y+h, x]).tolist())])
					face_encoding = face_recognition.face_encodings(frame, face_loc)
					matches = face_recognition.face_distance(known_face_encodings, face_encoding[0])
					name_index = np.argmin(matches)
					GPIO.output(16, GPIO.LOW)
					if (matches[name_index]<0.5):
						GPIO.output(12, GPIO.HIGH)
						#print("Known face")
						if known_face_pk[name_index] not in sended_face_pk:
							sended_face_pk.append(known_face_pk[name_index])
							crop_face = frame[y-50:y+h+50, x-50:x+w+50]
							Thread(target=sendPK, args=(name_index, crop_face, device_idn)).start()
							Timer(600, refreshSendedList, args=[known_face_pk[name_index]]).start()
					else:
						#print("Unknown face")
						GPIO.output(21, GPIO.HIGH)
						if unknown_face_encodings:
							matches = face_recognition.face_distance(np.array(unknown_face_encodings), face_encoding[0])
							name_index = np.argmin(matches)
							if (matches[0][name_index]<0.5):
								continue
							else:
								crop_face = frame[y-50:y+h+50, x-50:x+w+50]
								Thread(target=sendUnknown, args=(name_index, crop_face, device_idn)).start()
								unknown_face_encodings.append(face_encoding)
								Timer(600, refreshUnknownList, args=[face_encoding]).start()
						else:
							crop_face = frame[y-50:y+h+50, x-50:x+w+50]
							Thread(target=sendUnknown, args=(name_index, crop_face, device_idn)).start()
							unknown_face_encodings.append(face_encoding)
							Timer(600, refreshUnknownList, args=[face_encoding]).start()
			#checking movement
			Movement_B = False
			gray = cv2.GaussianBlur(gray, (21, 21), 0)
			if counter_motion_first == 0:
				firstFrame = gray
				counter_motion_first = 1
			if counter_motion == 20:
				firstFrame = gray
				counter_motion = 0
			frameDelta = cv2.absdiff(firstFrame, gray)
			thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
			thresh = cv2.dilate(thresh, None, iterations=2)
			cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
									cv2.CHAIN_APPROX_SIMPLE)
			cnts = imutils.grab_contours(cnts)
			for c in cnts:
				if cv2.contourArea(c) < 500:
					continue
				Movement_B = True
			if Movement_B:
				if datetime.now() > (movement_time+timedelta(seconds = 10)):
					t3 = Thread(target=sendMovement, args=(True, device_idn))
					t3.start()
					movement_time = datetime.now()
			counter_motion +=1
			GPIO.output(12, GPIO.LOW)
			GPIO.output(21, GPIO.LOW)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				global _FINISH
				_FINISH = True
				break
		except KeyboardInterrupt:
	 		GPIO.output(21, GPIO.LOW)
	 		GPIO.output(12, GPIO.LOW)
	 		GPIO.output(16, GPIO.LOW)
	 		break
	 		cv2.destroyAllWindows()
		except:
	 		pass
