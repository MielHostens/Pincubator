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
        self.HatcherMode = 0
        self.HatcherKp = 0.0
        self.HatcherKi = 0.0
        self.HatcherKd = 0.0
        self.HatcherMaxWindow = 1250.0
        self.HatcherMinWindow = 100.0


class structSettingsRX(object):
    def __init__(self):
        self.HatcherMode = 0
        self.HatcherKp = 0.0
        self.HatcherKi = 0.0
        self.HatcherKd = 0.0
        self.HatcherMaxWindow = 0.0
        self.HatcherMinWindow = 0.0
        self.HatcherPIDWindow = 0.0
        self.HatcherWindow = 0.0
        self.HatcherIntDSTempAverage = 0.0
        self.HatcherIntDSTemperature = 0.0
        self.HatcherIntDSErrorCount = 0.0
        self.HatcherExtDSTempAverage = 0.0
        self.HatcherExtDSTemperature = 0.0
        self.HatcherExtDSErrorCount = 0.0
        self.HatcherSCD30Temperature = 0.0
        self.HatcherSCD30Humidity = 0.0
        self.HatcherSCD30CO2 = 0.0
        self.SetterDSTemperature = 0.0


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

def writeSettings(object_to_save):
    global setterTX
    with open('HatcherSettings.ini', 'wb') as output:
        pickle.dump(setterTX, output)
    logging.info("Settings saved")

def readSettings():
    with open('HatcherSettings.ini', 'rb') as input:
        p = pickle.load(input)
    return p

def pushData(client, timer, pushrx):
    global pushTimer
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "Hatcher Mode": pushrx.HatcherMode,
                                      "Hatcher Kp": pushrx.HatcherKp,
                                      "Hatcher Ki": pushrx.HatcherKi,
                                      "Hatcher Kd": pushrx.HatcherKd,
                                      "Hatcher Max Window":pushrx.HatcherMaxWindow,
                                      "Hatcher Min Window": pushrx.HatcherMinWindow,
                                      "Hatcher PID Window": pushrx.HatcherPIDWindow,
                                      "Hatcher Window": pushrx.HatcherWindow,
                                      "Hatcher Internal Temperature Average": pushrx.HatcherIntDSTempAverage,
                                      "Hatcher Internal Temperature DS18": pushrx.HatcherIntDSTemperature,
                                      "Hatcher Internal Error Count": pushrx.HatcherIntDSErrorCount,
                                      "Hatcher External Temperature Average": pushrx.HatcherExtDSTempAverage,
                                      "Hatcher External Temperature DS18": pushrx.HatcherExtDSTemperature,
                                      "Hatcher External Error Count": pushrx.HatcherExtDSErrorCount,
                                      "Hatcher Temperature SCD30": pushrx.HatcherSCD30Temperature,
                                      "Hatcher Humidity SCD30": pushrx.HatcherSCD30Humidity,
                                      "Hatcher CO2 SCD30": pushrx.HatcherSCD30CO2,
                                      "Setter Temperature DS18 Extra": pushrx.SetterDSTemperature
                                    }
                                }
                            )
        logging.info(msg="Data pushed to Thingsboard")

def main():

    global setterRX
    global setterTX

    try:
        port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM1"  # replace 0 with whatever default you want
        host = sys.argv[2] if len(sys.argv) > 1 else "localhost"

        client = TBDeviceMqttClient(host, "9aqkgXRwb56wOks7miIv")
        client.connect()
        client.subscribe_to_all_attributes(callback=callback)

        link = txfer.SerialTransfer(port)
        link.open()

        time.sleep(2)

        # Read last saved settings
        if os.path.exists("HatcherSettings.ini"):
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
            sendSize = link.tx_obj(setterTX.HatcherMode, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(setterTX.HatcherKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.HatcherKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.HatcherKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.HatcherMaxWindow, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(setterTX.HatcherMinWindow, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                setterRX.HatcherMode = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                setterRX.HatcherKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherMaxWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherMinWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherIntDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherIntDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherIntDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherExtDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherExtDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherExtDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherSCD30Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherSCD30Humidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.HatcherSCD30CO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                setterRX.SetterDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                pushData(client = client, timer=300, pushrx = setterRX)
                logging.info(msg = 'RX | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}'.format(
                    setterRX.HatcherMode,
                    setterRX.HatcherKp,
                    setterRX.HatcherKi,
                    setterRX.HatcherKd,
                    setterRX.HatcherMaxWindow,
                    setterRX.HatcherMinWindow,
                    setterRX.HatcherWindow,
                    setterRX.HatcherIntDSTempAverage,
                    setterRX.HatcherIntDSTemperature,
                    setterRX.HatcherIntDSErrorCount,
                    setterRX.HatcherExtDSTempAverage,
                    setterRX.HatcherExtDSTemperature,
                    setterRX.HatcherExtDSErrorCount,
                    setterRX.HatcherSCD30Temperature,
                    setterRX.HatcherSCD30Humidity,
                    setterRX.HatcherSCD30CO2,
                    setterRX.SetterDSTemperature
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