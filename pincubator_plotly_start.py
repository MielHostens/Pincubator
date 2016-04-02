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
time0 			= datetime.now()

GPIO.setup(pinOT1, GPIO.OUT)
GPIO.setup(pinOT2, GPIO.OUT)
GPIO.setup(pinOH1, GPIO.OUT)
GPIO.setup(pinOH2, GPIO.OUT)

GPIO.output(pinOT1, GPIO.HIGH)
GPIO.output(pinOT2, GPIO.HIGH)
GPIO.output(pinOH1, GPIO.HIGH)
GPIO.output(pinOH2, GPIO.HIGH)


#plotly
py.sign_in("miel.hostens", "gziwrbelt1")

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
try:
  while True:
    for i in range(1, 6):
        hum_i, temp_i = Adafruit_DHT.read_retry(sensor, pinI1)
        if hum_i is not None and temp_i is not None:
	   time0 = datetime.now()
	   print "Incubator conditions:", time0
           print "Temp:", round(temp_i, 1)
           print "Hum:", round(hum_i, 1)
           print " "
           if temp_i < 37.5:
                GPIO.output(pinOT1, GPIO.LOW)
                time.sleep(1)
                GPIO.output(pinOT2, GPIO.LOW)
           elif temp_i > 37.8:
                GPIO.output(pinOT1, GPIO.HIGH)
                time.sleep(1)
                GPIO.output(pinOT2, GPIO.HIGH)
           if hum_i < 55.0:
                GPIO.output(pinOH1, GPIO.LOW)
           elif hum_i > 60.0:
                GPIO.output(pinOH1, GPIO.HIGH)
        hum_h, temp_h = Adafruit_DHT.read_retry(sensor, pinI2)
        if hum_h is not None and temp_h is not None:
           print "Hatcher conditions:", time0
           print "Temp:", round(temp_h)
           print "Hum:",  round(hum_h)
           print " "
           if hum_h < 55.0:
                GPIO.output(pinOH2, GPIO.LOW)
           elif hum_h > 60:
                GPIO.output(pinOH2, GPIO.HIGH)
        time.sleep(8)
    TemperatureI = Scatter(
    	x=[time0],
    	y=[temp_i]
    )
    TemperatureH = Scatter(
    	x=[time0],
        y=[temp_h]
    )
    HumidityI = Scatter(
        x=[time0],
        y=[hum_i]
    )
    HumidityH = Scatter(
         x=[time0],
         y=[hum_h]
    )
    data = Data([TemperatureI, TemperatureH, HumidityI, HumidityH])
    plot_url = py.plot(data, filename='Pincubator', fileopt='extend', reconnect_on=(200, '', 408))
    
#    print "Checking Alarms"
#    if temp_i < 36:
#    	p.push("Incubator", "Temperature low", str(round(temp_i, 1)))
#    elif temp_i > 39:
#    	p.push("Incubator", "Temperatur high", str(round(temp_i, 1)))
#    if hum_i < 50:
#        p.push("Incubator", "Humidity low", str(round(hum_i, 1)))
#    elif hum_i > 70:
#        p.push("Incubator", "Humidity high", str(round(hum_i, 1)))
#    if temp_h < 36:
#        p.push("Incubator", "Temperature low", str(round(temp_h, 1)))
#    elif temp_h > 39:
#        p.push("Incubator", "Temperatur high", str(round(temp_h, 1)))
#    if hum_h < 50:
#        p.push("Incubator", "Humidity low", str(round(hum_h, 1)))
#    elif hum_h > 70:
#        p.push("Incubator", "Humidity high", str(round(hum_h, 1)))

    print "Send to Plotly@", time0
    print " "
except (KeyboardInterrupt, SystemExit):
  GPIO.cleanup()
except:
  pass
exit()

