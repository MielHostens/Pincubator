# Written by Miel Hostens
# Version 1.1.0 @ 18.04.2017
import os, sys, time, getopt, random, json
import pynma
import serial
from decimal import Decimal

# artik cloud import
import artikcloud
from artikcloud.rest import ApiException

from pprint import pprint
from datetime import datetime, date

DEFAULT_CONFIG_PATH = '/home/pi/projects/pincubator/config/config.json'

with open(DEFAULT_CONFIG_PATH, 'r') as config_file:
	config_artik = json.load(config_file)['Temperature']
	#config_nma = json.load(config_file)['NMA']

# Configure Oauth2 access_token for the client application.  Here w$
# the device token for the configuration
artikcloud.configuration = artikcloud.Configuration();
artikcloud.configuration.access_token = config_artik['deviceToken']

# We create an instance of the Message API class which provides
# the send_message() and get_last_normalized_messages() api call
# for our example
api_instance = artikcloud.MessagesApi()

# Device_message - data that is sent to your device
device_message = {}

# Set the 'device id' - value from your config.json file
device_sdid = config_artik['deviceId']


#### Serial bus

ser = serial.Serial('/dev/ttyACM0', 9600)


#### Timers

timer_hour 			= datetime.now()
timer_quarter		= datetime.now()

# Incubation alerts (37.2-37.5) hatching (37.5-37.6)
temp_min		= 37.3
temp_max		= 37.8
hum_min			= 50
hum_max			= 60

# function to determine if decimals are decimals
def is_number(s):
	try:
		float(s) # for int, long and float
	except ValueError:
		try:
			complex(s) # for complex
		except ValueError:
			return False
	return True


#p = pynma.PyNMA(config_nma["Key"])
p = pynma.PyNMA("YOUR NMA KEY")

print("Succesfully connected to Notify My Android")
print(" ")

p.push("Pincubator", "Alerting", "Activated", priority=1)

try:
	while True:
		print ("Serial reading")
		read_serial=str(ser.readline(140))
		print(read_serial)
		print("Reading the serial succesfull")
		if read_serial == "Turning the eggs":
			p.push("Incubator", "Rotation", str(datetime.now()), priority=1)
		else:
			print("Trying to extract DHT...")
			print("The length of the serial read is: " + str(len(read_serial)))
			if len(read_serial) > 110:
				print("Serial larger >110")
				if is_number(read_serial[11:16]) and is_number(read_serial[30:35]) and is_number(read_serial[108:113]):
					print("The values were extracted successfully")
					temp_int = Decimal(read_serial[30:35])
					hum_int = Decimal(read_serial[11:16])
					temp_ext_set = Decimal(read_serial[108:113])
					print("Internal temperature is: " + str(temp_int))
					print("Internal humidity is: " + str(hum_int))
					print("External temperature set at: " + str(temp_ext_set))
					if temp_int > temp_max:
						p.push("Pincubator", "Temperature Too High", "Temp=" + str(round(temp_int, 1)) + " Hum=" + str(round(hum_int, 1)), priority=2)
					elif temp_int < temp_min:
						p.push("Pincubator", "Temperature Too Low", "Temp=" + str(round(temp_int, 1)) + " Hum=" + str(round(hum_int, 1)), priority=2)
					if hum_int > hum_max:
						p.push("Pincubator", "Humidity  Too High", "Temp=" + str(round(temp_int, 1)) + " Hum=" + str(round(hum_int, 1)), priority=2)
					elif hum_int < hum_min:
						p.push("Pincubator", "Temperature Too Low", "Temp=" + str(round(temp_int, 1)) + " Hum=" + str(round(hum_int, 1)), priority=2)
					print("Temperature and humidity checks succeeded")
					now = datetime.now()
					print("Current timestamp: " + str(now))
					deltatime = now-timer_hour
					print("Current delta time: " + str(deltatime.seconds))
					if deltatime.seconds > 3600:
						timer_hour = datetime.now()
						p.push("Incubator", "Notification", "Temp=" + str(round(temp_int, 1)) + " Hum=" + str(round(hum_int, 1)), priority=0)
					deltatime2 = now - timer_quarter
					if deltatime2.seconds > 900:
						timer_quarter = datetime.now()
						device_message['temp'] = read_serial[30:35]
						device_message['hum'] = read_serial[11:16]
						ts = int(time.time() * 1000)
						data = artikcloud.Message(device_message, device_sdid, ts)
						try:
							# Send Message
							print(data)
							print("Sending data ...")
							api_response = api_instance.send_message(data)
							print("Data sent") 
							# pprint(api_response)
						except ApiException as e:
							pprint("Exception when calling MessagesApi->send_message: %s\n" % e)
				else:
					print("The values were not extracted successfully")
			else:
				print("Serial read < 110 chars")
except (KeyboardInterrupt, SystemExit):
	p.push("Incubator", "Exiting", str(datetime.now()), priority=2)
	print("exiting...")  
except:
  pass
exit()

