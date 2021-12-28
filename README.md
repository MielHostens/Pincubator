# Pincubator version 3

Pincubator is a raspberry pi project together with 2 arduino mega modules to drive a DIY egg incubator (seperate setter and hatcher)

I found out after last year that using the raspberry as microcontroller is often challenging. 
I decided to include 2 arduino mega's as microcontroller. One for the setter, one for the hatcher. 

## See live when incubating

[Backstreet farm](http://backstreetfarm.ddns.net:8080/)
* login : public@backstreetfarm.com
* pw : Pincubator

## Hardware setup

1. [Arduino MEGA](https://store.arduino.cc/collections/arduino/products/arduino-mega-2560-rev3)
2. [Dalas temperature sensor](https://esphome.io/components/sensor/dallas.html)
3. [Sensirion CO2/RH/T module](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-scd30/)
3. [SSR](https://www.bitsandparts.nl/Relais-Solid-state-relais-3-32V-40A-24-380VAC-Fotek-SSR-40-DA-p101098)
3. [Eggs turning module](https://www.wingzstore.com/automatic-egg-turning-accessory.html)
4. 2 retired incubators
5. [Raspberry Pi](https://www.raspberrypi.org/products/model-b/)
6. Screwshields

I have multiple temperature sensors per device, and one extra from 'the other arduino', to allow failure detection.

![](./Pictures/ArduinoSetter.jpg)
![](./Pictures/ArduinoHatcher.jpg)
![](./Pictures/Electronics.jpg)

## Software setup

Each arduino talks to the raspberry pi over serial communication. That serial communication is forwarded to a local 
running [ThingsBoard](www.thingsboard.com) mqtt server. Settings on the server can be propagated back to the arduino to 
tuning of the setter and hatcher.

A [telegram bot](https://github.com/python-telegram-bot/python-telegram-bot) is installed allowing direct communication with the setter and hatcher.

### Setter

The setter is an old heavy incubator which was used for high temperatures.
 
![](./Pictures/Setter1.jpg) 

Ventilation is forced with 4 ventilators

![](./Pictures/Setter3.jpg)

* I changed the heater to a PWM of around 1000mS 
per 10 seconds. A [PID](https://playground.arduino.cc/Code/PIDLibrary/) controller is installed on the [Arduino MEGA](https://store.arduino.cc/collections/arduino/products/arduino-mega-2560-rev3) 
controlled throuh continuous [Dalas temperature sensor](https://esphome.io/components/sensor/dallas.html) 
temperature sensing. The PID algorythm changes the PWM using the [SSR](https://www.bitsandparts.nl/Relais-Solid-state-relais-3-32V-40A-24-380VAC-Fotek-SSR-40-DA-p101098).
* Humidity control is currently disabled 
* [Eggs turning](https://www.wingzstore.com/automatic-egg-turning-accessory.html) is done using a second SSR.

The script can be found in the [pincubator_v1_setter_folder](./pincubator_v1_setter.ino/pincubator_v1_setter.ino.ino).

### Hatcher

The setter is an old incubator with external heat chamber. 
* I put a Dalas temperature sensor in the external heat chamber at 40.1°C which keeps the internal 
chamber around 37.6°C (can be adjusted from [ThingsBoard server](localhost)). 
* An algorythm changes the external set-point according to hourly readings
* Humidity can be controlled using the [SSR](https://www.bitsandparts.nl/Relais-Solid-state-relais-3-32V-40A-24-380VAC-Fotek-SSR-40-DA-p101098).

### Raspberry pi

#### Installation

1. Install ThingsBoard community edition following online tutorial

2. You can create most devices and assets on the ThingsBoard server with 

```
cd Pincubator
initial_setup.py
```

3. Install all python packages

4. I have [no-ip.org](https://www.noip.com/support/knowledgebase/install-ip-duc-onto-raspberry-pi/) installed to allow remote control 

#### Runtime setter

A [Python 3.7](https://docs.python.org/3/whatsnew/3.7.html) process called [run_setter.py](/run_setter.py)

* The process connects to the serial readings of the Arduino via USB.
* Values are send to [ThingsBoard](https://127.0.0.1:8080/) to monitor the values over time
  Alerts can be set in the cloud dashboard.
* Telegram bot is initiated

```
cd Pincubator
nohup python3 run_setter.py > setter.out &
```

#### Runtime hatcher

A [Python 3.7](https://docs.python.org/3/whatsnew/3.7.html) process called [run_hatcher.py](/run_setter.py)

* The process connects to the serial readings of the Arduino via USB.
* Values are send to [ThingsBoard](https://127.0.0.1:8080/) to monitor the values over time
  Alerts can be set in the cloud dashboard.
* Telegram bot is NOT initiated

```
cd Pincubator
nohup python3 run_hatcher.py > hatcher.out &
```

