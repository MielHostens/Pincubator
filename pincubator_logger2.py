import os, sys, Adafruit_DHT, time
import mysql.connector
import logging

from mysql.connector import errorcode
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig()

sensor                       = Adafruit_DHT.AM2302 #DHT11/DHT22/AM2302
pin1                         = 4
pin2                         = 17
sensor_name1                 = "incubator-chamber"
sensor_name2                 = "hatching-chamber"
sec_between_log_entries      = 60
latest_humidity1	     = 0.0
latest_humidity2	     = 0.0
latest_temperature1	     = 0.0
latest_temperature2	     = 0.0
latest_value_datetime	     = None



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

def write_history():
	hum, temp = Adafruit_DHT.read_retry(sensor, pin1)
	write_latest_th(pin1, hum, temp)
	hum, temp = Adafruit_DHT.read_retry(sensor, pin2) 
	write_latest_th(pin2, hum, temp)

print "Ignoring first 2 sensor values to improve quality..."
for x in range(2):
  Adafruit_DHT.read_retry(sensor, pin1)
  Adafruit_DHT.read_retry(sensor, pin2)

print "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi..."
#create timer that is called every n seconds, without accumulating delays as when using sleep
scheduler = BackgroundScheduler()
scheduler.add_job(write_history, 'interval', seconds=sec_between_log_entries)
scheduler.start()
print "Started interval timer which will be called the first time in {0} seconds.".format(sec_between_log_entries);
exit()

