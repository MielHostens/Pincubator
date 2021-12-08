#!/usr/bin/env python3
import time
from pySerialTransfer import pySerialTransfer as txfer
from pypush import start_message, alert_message
from tb_gateway_mqtt import TBDeviceMqttClient
import logging
import pickle
import sys

pushTimer = time.time()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    SetterOnOff = 1
    HatcherOnOff = 0
    SetterPIDOnOff = 0
    HatcherPIDOnOff = 0
    SetterManualOnOff = 1
    HatcherManualOnOff = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    HatcherKp = 0.0
    HatcherKi = 0.0
    HatcherKd = 0.0
    SetterTempWindow = 250.0
    HatcherTempWindow = 250.0


def writeSettings(object_to_save):
    with open('Setting.ini', 'wb') as output:
        pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)
    logging.info("Settings saved")

def readSettings():
    with open('Setting.ini', 'rb') as input:
        p = pickle.load(input)
    return p

class structSettingsRX(object):
    SetterOnOff = 0
    HatcherOnOff = 0
    SetterPIDOnOff = 0
    HatcherPIDOnOff = 0
    SetterManualOnOff = 0
    HatcherManualOnOff = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    HatcherKp = 0.0
    HatcherKi = 0.0
    HatcherKd = 0.0
    SetterTempWindow = 0.0
    HatcherTempWindow = 0.0
    SetterPIDWindow = 0.0
    HatcherPIDWindow = 0.0
    SetterWindow = 0.0
    HatcherWindow = 0.0
    SetterDHTTempAverage = 0.0
    SetterDHTHumidity = 0.0
    SetterSCD30Temperature = 0.0
    SetterSCD30Humidity = 0.0
    SetterSCD30CO2 = 0.0
    SetterDS1Temperature = 0.0
    SetterDS2Temperature = 0.0
    HatcherIntDHTTempAverage = 0.0
    HatcherIntDHTHumidity = 0.0
    HatcherIntDSTemperature = 0.0
    HatcherCozirTemperature = 0.0
    HatcherCozirHumidity = 0.0
    HatcherCozirCO2 = 0


def callback(client, result, extra):
    logging.info("Settings update received")
    for key, value in result.items():
        # print(key, value)
        updateSettings(key, value)
        logging.info(msg="Settings updated for : " + key)

def updateSettings(key, value):
    if key.__contains__("OnOff"):
        setattr(structSettingsTX, key, int(value))
        logging.info("Settings for boolean adjusted")
    else:
        setattr(structSettingsTX, key, float(value))
        logging.info(msg="Settings for " + str(key) + " to value: " + str(value))
    writeSettings(structSettingsTX)

def pushData(client, timer):
    global pushTimer
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "SetterOnOff": structSettingsRX.SetterOnOff,
                                      "SetterTempWindow":structSettingsRX.SetterTempWindow,
                                      "SetterPIDWindow": structSettingsRX.SetterPIDWindow,
                                      "SetterWindow": structSettingsRX.SetterWindow,
                                      "SetterPIDOnOff": structSettingsRX.SetterPIDOnOff,
                                      "SetterManualOnOff": structSettingsRX.SetterManualOnOff,
                                      "Setter Temperature DHT22": structSettingsRX.SetterDHTTempAverage,
                                      "Setter Humidity DHT22": structSettingsRX.SetterDHTHumidity,
                                      "Setter Temperature SCD30": structSettingsRX.SetterSCD30Temperature,
                                      "Setter Humidity SCD30": structSettingsRX.SetterSCD30Humidity,
                                      "Setter CO2 SCD30": structSettingsRX.SetterSCD30CO2,
                                      "Setter Temperature DS18 1": structSettingsRX.SetterDS1Temperature,
                                      "Setter Temperature DS18 2": structSettingsRX.SetterDS2Temperature,
                                      "Setter Kp": structSettingsRX.SetterKp,
                                      "Setter Ki": structSettingsRX.SetterKi,
                                      "Setter Kd": structSettingsRX.SetterKd,
                                      "HatcherOnOff": structSettingsRX.HatcherOnOff,
                                      "HatcherTempWindow":structSettingsRX.HatcherTempWindow,
                                      "HatcherPIDWindow": structSettingsRX.HatcherPIDWindow,
                                      "HatcherWindow": structSettingsRX.HatcherWindow,
                                      "HatcherPIDOnOff": structSettingsRX.HatcherPIDOnOff,
                                      "HatcherManualOnOff":structSettingsRX.HatcherManualOnOff,
                                      "Hatcher Temperature DHT22": structSettingsRX.HatcherIntDHTTempAverage,
                                      "Hatcher Humidity DHT22": structSettingsRX.HatcherIntDHTHumidity,
                                      "Hatcher Temperature COZIR": structSettingsRX.HatcherCozirTemperature,
                                      "Hatcher Humidity COZIR": structSettingsRX.HatcherCozirHumidity,
                                      "Hatcher CO2 COZIR": structSettingsRX.HatcherCozirCO2,
                                      "Hatcher Temperature DS18": structSettingsRX.HatcherIntDSTemperature,
                                      "Hatcher Kp": structSettingsRX.HatcherKp,
                                      "Hatcher Ki": structSettingsRX.HatcherKi,
                                      "Hatcher Kd": structSettingsRX.HatcherKd
                                    }
                                }
                            )

def checkSetter(data, interval):
    global setterCheckTime
    if abs(time.time() - setterCheckTime) > interval:
        logging.info("Checking Setter")
        if "SetterTempAverage" in data:
            if float(data["SetterTempAverage"]) < 36.0:
                alert_message("Setter TEMPERATURE is too low: " + data["SetterTempAverage"])
                logging.info("Alert message sent")
        if "SetterTempAverage" in data:
            if float(data["SetterTempAverage"]) > 38.5:
                alert_message("Setter TEMPERATURE too high: " + data["SetterTempAverage"])
                logging.info("Alert message sent")
        if "SetterHumidity" in data:
            if float(data["SetterHumidity"]) < 10.0:
                alert_message("Setter HUMIDITY is too low: " + data["SetterHumidity"])
                logging.info("Alert message sent")
        if "SetterCozirCO2" in data:
            if float(data["SetterCozirCO2"]) > 5000.0:
                alert_message("Setter CO2 is too High: " + data["SetterCozirCO2"])
                logging.info("Alert message sent")
        setterCheckTime = time.time()

def checkHatcher(data, interval):
    global hatcherCheckTime
    if abs(time.time() - hatcherCheckTime) > interval:
        logging.info("Checking Hatcher")
        if "HatcherIntTempAverage" in data:
            if float(data["HatcherIntTempAverage"]) < 36.0:
                alert_message("Hatcher TEMPERATURE is too low: " + data["HatcherIntTempAverage"])
                logging.info("Alert message sent")
        if "HatcherIntTempAverage" in data:
            if float(data["HatcherIntTempAverage"]) > 38.5:
                alert_message("Hatcher TEMPERATURE too high: " + data["HatcherIntTempAverage"])
                logging.info("Alert message sent")
        if "HatcherIntHumidity" in data:
            if float(data["HatcherIntHumidity"]) < 10.0:
                alert_message("Hatcher HUMIDITY is too low: " + data["HatcherIntHumidity"])
                logging.info("Alert message sent")
        if "HatcherCozirCO2" in data:
            if float(data["HatcherCozirCO2"]) > 5000.0:
                alert_message("Hatcher CO2 is too High: " + data["HatcherCozirCO2"])
                logging.info("Alert message sent")
        hatcherCheckTime = time.time()

def dict_clean(items):
    result = {}
    for key, value in items:
        if value is None:
            value = 0
        result[key] = value
    return result

def main():

    try:
        port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"  # replace 0 with whatever default you want
        host = sys.argv[2] if len(sys.argv) > 1 else "localhost"
        client = TBDeviceMqttClient(host, "MetUfDYMrXno9RKiiGl7")
        client.connect()
        client.subscribe_to_all_attributes(callback=callback)


        link = txfer.SerialTransfer(port)
        link.open()

        time.sleep(2)

        # Finish by sending message
        # start_message()

        # Read last saved settings
        structSettingsTX = readSettings()

        logging.info("Setup OK")
        while True:
            sendSize = 0
            sendSize = link.tx_obj(structSettingsTX.SetterOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.HatcherOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.SetterPIDOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.HatcherPIDOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.SetterManualOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.HatcherManualOnOff, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.SetterKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.SetterTempWindow, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherTempWindow, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                structSettingsRX.SetterOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.HatcherOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.SetterPIDOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.HatcherPIDOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.SetterManualOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.HatcherManualOnOff = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.SetterKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterTempWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherTempWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDHTTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDHTHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
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

                structSettingsRX.HatcherIntDHTTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherIntDHTHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherIntDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherCozirTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherCozirHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherCozirCO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                pushData(client = client, timer=60)
                logging.info(msg = 'RX | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}'.format(
                    structSettingsRX.SetterOnOff,
                    structSettingsRX.HatcherOnOff,
                    structSettingsRX.SetterPIDOnOff,
                    structSettingsRX.HatcherPIDOnOff,
                    structSettingsRX.SetterManualOnOff,
                    structSettingsRX.HatcherManualOnOff,
                    structSettingsRX.SetterKp,
                    structSettingsRX.SetterKi,
                    structSettingsRX.SetterKd,
                    structSettingsRX.HatcherKp,
                    structSettingsRX.HatcherKi,
                    structSettingsRX.HatcherKd,
                    structSettingsRX.SetterTempWindow,
                    structSettingsRX.HatcherTempWindow,
                    structSettingsRX.SetterWindow,
                    structSettingsRX.HatcherWindow,
                    structSettingsRX.SetterDHTTempAverage,
                    structSettingsRX.SetterDHTHumidity,
                    structSettingsRX.SetterSCD30Temperature,
                    structSettingsRX.SetterSCD30Humidity,
                    structSettingsRX.SetterSCD30CO2,
                    structSettingsRX.SetterDS1Temperature,
                    structSettingsRX.SetterDS2Temperature,
                    structSettingsRX.HatcherIntDHTTempAverage,
                    structSettingsRX.HatcherIntDSTemperature,
                    structSettingsRX.HatcherIntDHTHumidity,
                    structSettingsRX.HatcherCozirTemperature,
                    structSettingsRX.HatcherCozirHumidity,
                    structSettingsRX.HatcherCozirCO2
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

            #if int(settings["PushOnOff"]) == 199:
            #    logging.info("Push notifications Off")
            #else:
            #    logging.info("Push notifications On")
                #interval = int(settings["PushOnOff"])
                #if int(settings["SetterOnOff"]) == 1:
                #    logging.info("Checking setter")
                #    checkSetter(data_incubator, interval * 60)
                #if int(settings["HatcherOnOff"]) == 1:
                #    logging.info("Checking hatcher")
                #    checkHatcher(data_incubator, interval * 60)

    except KeyboardInterrupt:
        link.close()


if __name__ == '__main__':
    main()