import os, sys, Adafruit_DHT, time
import mysql.connector
import logging
import RPi.GPIO as GPIO

from mysql.connector import errorcode
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig()
GPIO.setmode(GPIO.BCM)

sensor	                = Adafruit_DHT.AM2302 #DHT11/DHT22/AM2302
pinI1                   = 17
pinI2                   = 18
pinOT1			= 27
pinOT2			= 22
pinOH1			= 23
pinOH2			= 24
sec_between_log_entries = 60
latest_humidity1        = 0.0
latest_humidity2        = 0.0
latest_temperature1     = 0.0
latest_temperature2     = 0.0
latest_value_datetime   = None

GPIO.setup(pinOT1, GPIO.OUT)
GPIO.setup(pinOT2, GPIO.OUT)
GPIO.setup(pinOH1, GPIO.OUT)
GPIO.setup(pinOH2, GPIO.OUT)

GPIO.output(pinOT1, GPIO.HIGH)
GPIO.output(pinOT2, GPIO.HIGH)
GPIO.output(pinOH1, GPIO.HIGH)
GPIO.output(pinOH2, GPIO.HIGH)

cnx = mysql.connector.connect(user='root', password='bdyCm1;',host='127.0.0.1', database='pincubator')
cursor = cnx.cursor()

def write_latest_th(sensor_id, curr_temp, curr_hum):
	add_th= ("INSERT INTO tbl_sensordata "
              "(sensor_date, sensor, temp, hum) "
              "VALUES (%(date)s, %(sensor)s, %(temp)s, %(hum)s)")
	data_th= {
		'date': datetime.now(),
		'sensor': sensor_id,
		'temp': curr_temp,
		'hum': curr_hum
	}
	cursor.execute(add_th, data_th)
	cnx.commit()

print "Ignoring first 2 sensor values to improve quality..."
for x in range(2):
  Adafruit_DHT.read_retry(sensor, pinI1)
  Adafruit_DHT.read_retry(sensor, pinI1)

print "Starting loop..."
try:
  while True:
    for i in range(1, 6):
    	hum, temp = Adafruit_DHT.read_retry(sensor, pinI1)
    	if hum is not None and temp is not None:
       	   print "Incubator conditions:", datetime.now()
	   print "Temp:", temp
	   print "Hum:", hum
	   print " "
	   if temp < 37.7:
		GPIO.output(pinOT1, GPIO.LOW)
		time.sleep(1)
		GPIO.output(pinOT2, GPIO.LOW)
	   elif temp > 38.3:
		GPIO.output(pinOT1, GPIO.HIGH)
		time.sleep(1)
		GPIO.output(pinOT2, GPIO.HIGH)
	   if hum < 57.0:
		GPIO.output(pinOH1, GPIO.LOW)
	   elif hum > 60.0:
		GPIO.output(pinOH1, GPIO.HIGH)
	hum, temp = Adafruit_DHT.read_retry(sensor, pinI2)
	if hum is not None and temp is not None:
           print "Hatcher conditions:", datetime.now()
	   print "Temp:", temp 
	   print "Hum:",  hum
	   print " "
	   if hum < 57.0:
		GPIO.output(pinOH2, GPIO.LOW)
	   elif hum > 60:
		GPIO.output(pinOH2, GPIO.HIGH)
	time.sleep(10)
    hum, temp = Adafruit_DHT.read_retry(sensor, pinI1)
    write_latest_th(pinI1, temp, hum)
    hum, temp = Adafruit_DHT.read_retry(sensor, pinI1)
    write_latest_th(pinI1, temp, hum)
except (KeyboardInterrupt, SystemExit):
  GPIO.cleanup()
exit()
