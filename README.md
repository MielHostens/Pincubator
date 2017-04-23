# Pincubator version 2
Pincubator is a raspberry pi project together with arduino module to drive a DIY egg incubator

I found out after last year that using the raspberry as microcontroller is often challenging. I decided this year to include the arduino as microcontroller.

## Hardware setup

1. [Arduino UNO](https://www.arduino.cc/en/Main/arduinoBoardUno)
2. [DHT22](https://www.adafruit.com/product/385)
3. [8 relay board module](https://www.sainsmart.com/8-channel-dc-5v-relay-module-for-arduino-pic-arm-dsp-avr-msp430-ttl-logic.html)
3. [Eggs turning module](https://www.wingzstore.com/automatic-egg-turning-accessory.html)
4. Retired incubator
5. [Raspberry Pi](https://www.raspberrypi.org/products/model-b/)

I have extra humidity and temperature meters in the internal chamber to ensure DHT22 measurements

## Software setup

Current setup

### Arduino microcontroller

An [Arduino UNO](https://www.arduino.cc/en/Main/arduinoBoardUno) with [DHT22](https://www.adafruit.com/product/385) temperature and humidity sensor to control via [8 relay board module](https://www.sainsmart.com/8-channel-dc-5v-relay-module-for-arduino-pic-arm-dsp-avr-msp430-ttl-logic.html)

* Temperature control (2 chambered incubator, external chamber is temp controlled to get stable internal chamber)
* Humidity control (extra ventilation on water surface, although fogger would be prefered, next to do)
* [Eggs turning module](https://www.wingzstore.com/automatic-egg-turning-accessory.html)
* Ventilation control

The script can be found in the [arduino_incubator folder](./arduino_incubator).

### Raspberry pi

[Python 3.6](https://docs.python.org/3/whatsnew/3.6.html) process called [pincubator_alerter.py](/pincubator_alerter.py)

* The process connects to the serial readings of the Arduino via USB.
* Values are send to [Artik cloud](https://artik.cloud/) each 15 minutes to monitor the values over time
  Alerts can be set in the cloud dashboard. You have include a config folder with config.json file containing your artik cloud settings

```
{
    "Temperature": {
      "deviceId": "YOUR DEVICE ID",
      "deviceToken": "YOUR DEVICE TOKEN"
    }
  }
```  

* Reading are compared to temperature and humidity settings and if they differ to much a message is sent via [Notify My Android](http://www.notifymyandroid.com/)

Python process is continuously monitored with [supervisord](http://supervisord.org/), to ensure restart on failure