import laptop
import databaseMain as dbMain
import dbMotion
import dbRecognition
import dbActivity
import getEncodings
import threading
import time, traceback
import json
from logfile import *

with open('/home/pi/koraupdater/token.json', 'r') as f:
    token = json.load(f)

auth_token = token['token']
header = {'Authorization': 'Token ' + auth_token}
device_idn = token['id']

def sendToServer():
    print(laptop._FINISH)
    global auth_token
    global header
    global device_idn
    log_database_changes("Activity Data sending")
    dbActivity.sendData(auth_token, header, device_idn)
    log_database_changes("Motion Data sending")
    dbMotion.sendData(auth_token, header, device_idn)
    log_database_changes("Checks Data sending")
    dbRecognition.sendData(auth_token, header, device_idn)
    if not laptop._FINISH:
        threading.Timer(60, sendToServer).start()

dbMain.databaseInit()
dbMotion.checkTable()
dbActivity.checkTable()
dbRecognition.checkTable()
getEncodings.checkTable()

getEncodings.refreshEncodings(auth_token, header, device_idn)

sendToServer()
laptop.sendActivity(device_idn)

laptop.saveEncodings()
laptop.startRecognition(device_idn)
