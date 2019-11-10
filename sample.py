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
import requests
import os 
with open('/home/pi/koraupdate/token.json', 'r') as f:
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

def updater():
    try:
        r = requests.get("https://www.kora.work/api/updated/"+device_idn, headers=header, timeout = 10)
        print(r.text)
        status = json.loads(r.text)
        if status['success']:
            os.system("python3 /home/pi/koraupdate/updater.py")
        threading.Timer(600, updater).start()
    except:
        pass
def encodingsUpdate():
    getEncodings.refreshEncodings(auth_token, header, device_idn)
    threading.Timer(1800, encodingsUpdate).start()


threading.Timer(0, updater).start()

encodingsUpdate()

dbMain.databaseInit()
dbMotion.checkTable()
dbActivity.checkTable()
dbRecognition.checkTable()
getEncodings.checkTable()



sendToServer()
laptop.sendActivity(device_idn)

laptop.saveEncodings()
laptop.startRecognition(device_idn)
