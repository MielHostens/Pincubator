#!/usr/bin/env python3
import time
from pySerialTransfer import pySerialTransfer as txfer
from tb_gateway_mqtt import TBDeviceMqttClient
import logging
import pickle
import sys

pushTimer = time.time()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    SetterMode = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    SetterMaxWindow = 1250.0
    SetterMinWindow = 100.0


class structSettingsRX(object):
    SetterMode = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    SetterMaxWindow = 0.0
    SetterMinWindow = 0.0
    SetterPIDWindow = 0.0
    SetterWindow = 0.0
    SetterTemperatureAverage = 0.0
    SetterDHTTemperature = 0.0
    SetterDHTHumidity = 0.0
    SetterSCD30Temperature = 0.0
    SetterSCD30Humidity = 0.0
    SetterSCD30CO2 = 0.0
    SetterDS1Temperature = 0.0
    SetterDS2Temperature = 0.0
    SetterErrorCount = 0.0
    HatcherDS1Temperature = 0.0


def callback(client, result, extra):
    logging.info("Settings update received")
    for key, value in result.items():
        # print(key, value)
        updateSettings(key, value)
        logging.info(msg="Settings updated for : " + key)

def updateSettings(key, value):
    if key.__contains__("Mode"):
        setattr(structSettingsTX, key, int(value))
        logging.info("Settings for mode adjusted")
    else:
        setattr(structSettingsTX, key, float(value))
        logging.info(msg="Settings for " + str(key) + " to value: " + str(value))
    writeSettings(structSettingsTX)

def writeSettings(object_to_save):
    with open('SetterSettings.ini', 'wb') as output:
        pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)
    logging.info("Settings saved")

def readSettings():
    with open('SetterSettings.ini', 'rb') as input:
        p = pickle.load(input)
    return p

def pushData(client, timer):
    global pushTimer
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "Setter Mode": structSettingsRX.SetterMode,
                                      "Setter Max Window":structSettingsRX.SetterMaxWindow,
                                      "Setter Min Window": structSettingsRX.SetterMinWindow,
                                      "Setter PID Window": structSettingsRX.SetterPIDWindow,
                                      "Setter Window": structSettingsRX.SetterWindow,
                                      "Setter Temperature Average": structSettingsRX.SetterTemperatureAverage,
                                      "Setter Temperature DHT22": structSettingsRX.SetterDHTTemperature,
                                      "Setter Humidity DHT22": structSettingsRX.SetterDHTHumidity,
                                      "Setter Temperature SCD30": structSettingsRX.SetterSCD30Temperature,
                                      "Setter Humidity SCD30": structSettingsRX.SetterSCD30Humidity,
                                      "Setter CO2 SCD30": structSettingsRX.SetterSCD30CO2,
                                      "Setter Temperature DS18 1": structSettingsRX.SetterDS1Temperature,
                                      "Setter Temperature DS18 2": structSettingsRX.SetterDS2Temperature,
                                      "Setter Kp": structSettingsRX.SetterKp,
                                      "Setter Ki": structSettingsRX.SetterKi,
                                      "Setter Kd": structSettingsRX.SetterKd,
                                      "Setter Error Count": structSettingsRX.SetterErrorCount,
                                      "Hatcher Temperature DS18 Extra": structSettingsRX.HatcherDS1Temperature
                                    }
                                }
                            )
        logging.info(msg="Data pushed to Thingsboard")

def main():

    try:
        port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"  # replace 0 with whatever default you want
        host = sys.argv[2] if len(sys.argv) > 1 else "localhost"
        client = TBDeviceMqttClient(host, "MetUfDYMrXno9RKiiGl7")
        #client = TBDeviceMqttClient(host, "8bkAvBZ5JS8aqCM0qQ4j")
        client.connect()
        client.subscribe_to_all_attributes(callback=callback)


        link = txfer.SerialTransfer(port)
        link.open()

        time.sleep(2)

        # Read last saved settings
        structSettingsTX = readSettings()
        logging.info(msg='Start settings | {} | {} | {} | {} | {} | {} '.format(
            structSettingsTX.SetterMode,
            structSettingsTX.SetterKp,
            structSettingsTX.SetterKi,
            structSettingsTX.SetterKd,
            structSettingsTX.SetterMaxWindow,
            structSettingsTX.SetterMinWindow
            )
        )
        logging.info("Setup OK")
        while True:
            sendSize = 0
            sendSize = link.tx_obj(structSettingsTX.SetterMode, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.SetterKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterMaxWindow, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterMinWindow, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                structSettingsRX.SetterMode = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.SetterKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterMaxWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterMinWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDHTTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDHTHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterTemperatureAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterSCD30Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterSCD30Humidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterSCD30CO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDS1Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDS2Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherDS1Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                pushData(client = client, timer=300)
                logging.info(msg = 'RX|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}'.format(
                    structSettingsRX.SetterMode,
                    structSettingsRX.SetterKp,
                    structSettingsRX.SetterKi,
                    structSettingsRX.SetterKd,
                    structSettingsRX.SetterMaxWindow,
                    structSettingsRX.SetterMinWindow,
                    structSettingsRX.SetterWindow,
                    structSettingsRX.SetterTemperatureAverage,
                    structSettingsRX.SetterDHTTemperature,
                    structSettingsRX.SetterDHTHumidity,
                    structSettingsRX.SetterSCD30Temperature,
                    structSettingsRX.SetterSCD30Humidity,
                    structSettingsRX.SetterSCD30CO2,
                    structSettingsRX.SetterDS1Temperature,
                    structSettingsRX.SetterDS2Temperature,
                    structSettingsRX.SetterErrorCount,
                    structSettingsRX.HatcherDS1Temperature
                    )
                )

            elif link.status < 0:
                if link.status == txfer.CRC_ERROR:
                    print('ERROR: CRC_ERROR')
                elif link.status == txfer.PAYLOAD_ERROR:
                    print('ERROR: PAYLOAD_ERROR')
                elif link.status == txfer.STOP_BYTE_ERROR:
                    print('ERROR: STOP_BYTE_ERROR')
                else:
                    print('ERROR: {}'.format(link.status))

    except KeyboardInterrupt:
        link.close()

if __name__ == '__main__':
    main()