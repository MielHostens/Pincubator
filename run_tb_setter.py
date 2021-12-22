#!/usr/bin/env python3
from pySerialTransfer import pySerialTransfer as txfer
from tb_gateway_mqtt import TBDeviceMqttClient
import sys, json, codecs, os, time, logging, pickle


pushTimer = time.time()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    def __init__(self):
        self.SetterMode = 0  # an instance attribute
        self.SetterKp = 0.0  # an instance attribute
        self.SetterKi = 0.0  # an instance attribute
        self.SetterKd = 0.0  # an instance attribute
        self.SetterMaxWindow = 1250.0  # an instance attribute
        self.SetterMinWindow = 100.0


class structSettingsRX(object):
    def __init__(self):
        self.SetterMode = 0
        self.SetterKp = 0.0
        self.SetterKi = 0.0
        self.SetterKd = 0.0
        self.SetterMaxWindow = 0.0
        self.SetterMinWindow = 0.0
        self.SetterPIDWindow = 0.0
        self.SetterWindow = 0.0
        self.SetterTemperatureAverage = 0.0
        self.SetterDHTTemperature = 0.0
        self.SetterDHTHumidity = 0.0
        self.SetterSCD30Temperature = 0.0
        self.SetterSCD30Humidity = 0.0
        self.SetterSCD30CO2 = 0.0
        self.SetterDS1Temperature = 0.0
        self.SetterDS2Temperature = 0.0
        self.SetterErrorCount = 0.0
        self.HatcherDS1Temperature = 0.0

setterTX = structSettingsTX()
setterRX = structSettingsRX()

def callback(client, result, extra):
    logging.info("Settings update received")
    for key, value in result.items():
        # print(key, value)
        updateSettings(key, value)
        logging.info(msg="Settings updated for : " + key)

def updateSettings(key, value):
    global setterTX
    if key.__contains__("Mode"):
        setattr(setterTX, key, int(value))
        logging.info("Settings for mode adjusted")
    else:
        setattr(setterTX, key, float(value))
        logging.info(msg="Settings for " + str(key) + " to value: " + str(value))
    writeSettings()

def writeSettings():
    global setterTX
    with open('SetterSettings.ini', 'wb') as output:
        pickle.dump(setterTX, output)
    logging.info("Settings saved")

def readSettings():
    with open('SetterSettings.ini', 'rb') as input:
        p = pickle.loads(input)
    return p

def pushData(client, timer):
    global pushTimer
    global setterRX
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "Setter Mode": setterRX.SetterMode,
                                      "Setter Max Window":setterRX.SetterMaxWindow,
                                      "Setter Min Window": setterRX.SetterMinWindow,
                                      "Setter PID Window": setterRX.SetterPIDWindow,
                                      "Setter Window": setterRX.SetterWindow,
                                      "Setter Temperature Average": setterRX.SetterTemperatureAverage,
                                      "Setter Temperature DHT22": setterRX.SetterDHTTemperature,
                                      "Setter Humidity DHT22": setterRX.SetterDHTHumidity,
                                      "Setter Temperature SCD30": setterRX.SetterSCD30Temperature,
                                      "Setter Humidity SCD30": setterRX.SetterSCD30Humidity,
                                      "Setter CO2 SCD30": setterRX.SetterSCD30CO2,
                                      "Setter Temperature DS18 1": setterRX.SetterDS1Temperature,
                                      "Setter Temperature DS18 2": setterRX.SetterDS2Temperature,
                                      "Setter Kp": setterRX.SetterKp,
                                      "Setter Ki": setterRX.SetterKi,
                                      "Setter Kd": setterRX.SetterKd,
                                      "Setter Error Count": setterRX.SetterErrorCount,
                                      "Hatcher Temperature DS18 Extra": setterRX.HatcherDS1Temperature
                                    }
                                }
                            )
        logging.info(msg="Data pushed to Thingsboard")

def main():

    global SetterRX
    global SetterTX

    try:
        port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"  # replace 0 with whatever default you want
        host = sys.argv[2] if len(sys.argv) > 1 else "localhost"

        client = TBDeviceMqttClient(host, "MetUfDYMrXno9RKiiGl7")
        client.connect()
        client.subscribe_to_all_attributes(callback=callback)

        link = txfer.SerialTransfer(port)
        link.open()

        time.sleep(2)

        # Read last saved settings
        if os.path.exists("SetterSettings.ini"):
            setterTX = readSettings()
        else:
            setterTX = structSettingsTX()

        setterRX = structSettingsRX()

        logging.info(msg='Start settings | {} | {} | {} | {} | {} | {} '.format(
            setterTX.SetterMode,
            setterTX.SetterKp,
            setterTX.SetterKi,
            setterTX.SetterKd,
            setterTX.SetterMaxWindow,
            setterTX.SetterMinWindow
            )
        )
        logging.info("Setup OK")
        while True:
            sendSize = 0
            sendSize = link.tx_obj(setterTX.SetterMode, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(setterTX.SetterKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.SetterKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.SetterKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.SetterMaxWindow, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.SetterMinWindow, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                setterRX.SetterMode = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                setterRX.SetterKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterMaxWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterMinWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterDHTTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterDHTHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterTemperatureAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterSCD30Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterSCD30Humidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterSCD30CO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterDS1Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterDS2Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherDS1Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                pushData(client = client, timer=300)
                logging.info(msg = 'RX|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}'.format(
                    setterRX.SetterMode,
                    setterRX.SetterKp,
                    setterRX.SetterKi,
                    setterRX.SetterKd,
                    setterRX.SetterMaxWindow,
                    setterRX.SetterMinWindow,
                    setterRX.SetterWindow,
                    setterRX.SetterTemperatureAverage,
                    setterRX.SetterDHTTemperature,
                    setterRX.SetterDHTHumidity,
                    setterRX.SetterSCD30Temperature,
                    setterRX.SetterSCD30Humidity,
                    setterRX.SetterSCD30CO2,
                    setterRX.SetterDS1Temperature,
                    setterRX.SetterDS2Temperature,
                    setterRX.SetterErrorCount,
                    setterRX.HatcherDS1Temperature
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