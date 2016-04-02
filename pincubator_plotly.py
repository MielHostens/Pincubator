# Written by Miel Hostens
# Version 0.1.0 @ 22.02.2015
import os, sys, Adafruit_DHT, time
import RPi.GPIO as GPIO
import plotly.plotly as py
import pynma

from datetime import datetime, date
from plotly.graph_objs import *

GPIO.setmode(GPIO.BCM)

sensor                  = Adafruit_DHT.AM2302 #DHT11/DHT22/AM2302
pinI1                   = 18
pinI2                   = 17
pinOT1                  = 27
pinOT2                  = 22
pinOH1                  = 24
pinOH2                  = 23
pinOR			= 25
timer			= 0
alarm_i			= 0
alarm_h			= 0
# incubation (37.2-37.5) hatching (37.5-37.6)
temp_min		= 37.2
temp_max		= 38.2
hum_i_min		= 50
hum_i_max		= 60
hum_h_min		= 80
hum_h_max		= 90
rotsec			= 12
temp_o			=0
hum_i_o			=0
hum_h_o			=0

GPIO.setup(pinOT1, GPIO.OUT)
GPIO.setup(pinOT2, GPIO.OUT)
GPIO.setup(pinOH1, GPIO.OUT)
GPIO.setup(pinOH2, GPIO.OUT)
GPIO.setup(pinOR, GPIO.OUT)

GPIO.output(pinOT1, GPIO.HIGH)
GPIO.output(pinOT2, GPIO.LOW)
GPIO.output(pinOH1, GPIO.HIGH)
GPIO.output(pinOH2, GPIO.LOW)
GPIO.output(pinOR, GPIO.HIGH)

#one rotation
GPIO.output(pinOR, GPIO.LOW)
time.sleep(rotsec)
GPIO.output(pinOR, GPIO.HIGH)
lastrotation = datetime.now()



print "Succesfully connected to Plot.ly"
#nma
p = pynma.PyNMA("a049cdfd83ac44724d615ad756b16ab2387be1abf184ae0f")
print "Succesfully connected to Notify My Android"
print " "
print "Ignoring first 2 sensor values to improve quality..."
for x in range(2):
  Adafruit_DHT.read_retry(sensor, pinI1)
  Adafruit_DHT.read_retry(sensor, pinI2)

print "Starting loop..."
p.push("Incubator", "Incubator starting", "Hatching started", priority=2)
try:
  while True:
    for i in range(1, 6):
        hum_i, temp_i = Adafruit_DHT.read_retry(sensor, pinI1)
        hum_h, temp_h = Adafruit_DHT.read_retry(sensor, pinI2)
	if hum_i is None and temp_i is None:
           p.push("Incubator", "Sensor Alarm", "Sensor hatcher is used from now", priority=2)
	   temp_i = temp_h
	   hum_i = hum_h
	elif hum_h is None and temp_h is None:
           p.push("Hatcher", "Sensor Alarm", "Sensor incubator is used from now", priority=2)
           temp_h = temp_i
           hum_h = hum_i
	else:
	   time0 = datetime.now()
	   print "Incubator conditions:", time0
           print "Temp:", round(temp_i, 1)
           print "Hum:", round(hum_i, 1)
           print " "
           if temp_i < temp_min:
                GPIO.output(pinOT1, GPIO.LOW)
                temp_o = 1
                if i ==1:
		   p.push("Low Temperature", "T:" + str(round(temp_i, 1)) + " H:"+ str(round(hum_i, 1)) + " T_H:" + str(round(temp_h,1)) + " H_H:" + str(round(hum_h,1)), "Temperature switched on", priority=1)
	   elif temp_i > temp_max:
                GPIO.output(pinOT1, GPIO.HIGH)
		temp_o = 0
                if i ==1:
		   p.push("High Temperature", "T:" + str(round(temp_i, 1)) + " H:"+ str(round(hum_i, 1)) + " T_H:" + str(round(temp_h,1)) + " H_H:" + str(round(hum_h,1)), "Temperature switched off", priority=1)
           if hum_i < hum_i_min:
                GPIO.output(pinOH1, GPIO.LOW)
		hum_i_o = 3
                if i ==1:
		   p.push("Low Humidity", "T:" + str(round(temp_i, 1)) + " H:"+ str(round(hum_i, 1)) + " T_H:" + str(round(temp_h,1)) + " H_H:" + str(round(hum_h,1)), "Humidity ventilator switched on", priority=1)
           elif hum_i > hum_i_max:
                GPIO.output(pinOH1, GPIO.HIGH)
		hum_i_o = 2
                if i ==1:
		   p.push("High Humidity", "T:" + str(round(temp_i, 1)) + " H:"+ str(round(hum_i, 1)) + " T_H:" + str(round(temp_h,1)) + " H_H:" + str(round(hum_h,1)), "Humidity ventilator switched off", priority=1)
	   print "Hatcher conditions:", time0
           print "Temp:", round(temp_h, 1)
           print "Hum:",  round(hum_h, 1)
           print " "
        time.sleep(9)
    deltatime = time0-lastrotation
    if deltatime.seconds > 3600:
	GPIO.output(pinOR, GPIO.LOW)
	time.sleep(rotsec)
	GPIO.output(pinOR, GPIO.HIGH)
	lastrotation = datetime.now()
        p.push("Incubator", "Rotation", str(lastrotation), priority=1)
        p.push("Incubator", "Notification", "Temp=" + str(round(temp_i, 1)) + " Hum=" + str(round(hum_i, 1)), priority=1)
    print "Checking Alarms"
    if temp_i < 36 or temp_i > 39.5 or hum_i < 40 or hum_i > 65:
    	p.push("Incubator", "Alarm", "Temp=" + str(round(temp_i, 1)) + " Hum=" + str(round(hum_i, 1)) + " Alarm=" + str(alarm_i), priority=1)
	alarm_i=alarm_i+1
    else:
	if alarm_i==0:
	   alarm_i=0
	else:
	   alarm_i=alarm_i-1
    if alarm_i>5:
	p.push("Incubator", "Critical Alarm", str(alarm_i), priority=2)
	alarm_i=0
    print " "
except (KeyboardInterrupt, SystemExit):
  GPIO.cleanup()
except:
  pass
exit()
