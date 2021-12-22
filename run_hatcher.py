#!/usr/bin/env python3
from pySerialTransfer import pySerialTransfer as txfer
from tb_gateway_mqtt import TBDeviceMqttClient
import sys, json, codecs, os, time, logging, pickle, datetime
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

pushTimer = time.time()
LastSerial = datetime.datetime.now()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    def __init__(self):
        self.HatcherMode = 0
        self.HatcherTempTargetExtTemperature = 40.1
        self.HatcherTempTargetIntTemperature = 37.6
        self.HatcherTempTargetIntHumidity = 65.0


class structSettingsRX(object):
    def __init__(self):
        self.HatcherMode = 0
        self.HatcherTempTargetExtTemperature = 0.0
        self.HatcherTempTargetIntTemperature = 0.0
        self.HatcherTempTargetIntHumidity = 0.0
        self.HatcherTargetExtTemperature = 0.0
        self.HatcherTargetIntTemperature = 0.0
        self.HatcherTargetIntHumidity = 0.0
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


hatcherTX = structSettingsTX()
hatcherRX = structSettingsRX()

def callback(client, result, extra):
    logging.info("Settings update received")
    for key, value in result.items():
        # print(key, value)
        updateSettings(key, value)
        logging.info(msg="Settings updated for : " + key)

def updateSettings(key, value):
    global hatcherTX
    if key.__contains__("Mode"):
        setattr(hatcherTX, key, int(value))
        logging.info("Settings for mode adjusted")
    else:
        setattr(hatcherTX, key, float(value))
        logging.info(msg="Settings for " + str(key) + " to value: " + str(value))
    writeSettings()

def writeSettings():
    global hatcherTX
    with open('HatcherSettings.ini', 'wb') as output:
        pickle.dump(hatcherTX, output)
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
                                      "Hatcher Temp External Temperature Target": pushrx.HatcherTempTargetExtTemperature,
                                      "Hatcher Temp Internal Temperature Target": pushrx.HatcherTempTargetIntTemperature,
                                      "Hatcher Temp Internal Humidity Target": pushrx.HatcherTempTargetIntHumidity,
                                      "Hatcher External Temperature Target":pushrx.HatcherTargetExtTemperature,
                                      "Hatcher Internal Temperature Target": pushrx.HatcherTargetIntTemperature,
                                      "Hatcher Internal Humidity Target": pushrx.HatcherTargetIntHumidity,
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

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )

def hatcher(update: Update, context: CallbackContext) -> None:
    global hatcherRX
    """Send a message when the command /start is issued."""
    datediff = datetime.datetime.now() - LastSerial
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your HATCHER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {LastSerial}')
    update.message.reply_text(fr'That was {round(datediff.total_seconds(), 0)} seconds ago')
    update.message.reply_text(fr'My temperature currently is {round(hatcherRX.HatcherIntDSTempAverage,1)} °C')
    update.message.reply_text(fr'My humidity currently is {round(hatcherRX.HatcherSCD30Humidity, 1)} %')

    update.message.reply_markdown_v2(
        fr'Thanks for asking {user.mention_markdown_v2()}\! Anything else wanted?',
        reply_markup=ForceReply(selective=True),
    )

def setter(update: Update, context: CallbackContext) -> None:
    global hatcherRX
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your SETTER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {LastSerial}')
    update.message.reply_text(fr'The SETTER temperature currently is {round(hatcherRX.SetterDSTemperature, 1)} °C')

    update.message.reply_markdown_v2(
        fr'Thanks for asking {user.mention_markdown_v2()}\! Anything else wanted?',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text("No idea what you want from me")


def main():

    global hatcherRX
    global hatcherTX

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
            hatcherTX = readSettings()
        else:
            hatcherTX = structSettingsTX()
        hatcherRX = structSettingsRX()

        logging.info(msg='Start settings | {} | {} | {} | {} '.format(
            hatcherTX.HatcherMode,
            hatcherTX.HatcherTempTargetExtTemperature,
            hatcherTX.HatcherTempTargetIntTemperature,
            hatcherTX.HatcherTempTargetIntHumidity
            )
        )
        logging.info("Setup OK")
        while True:
            sendSize = 0
            sendSize = link.tx_obj(hatcherTX.HatcherMode, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(hatcherTX.HatcherTempTargetExtTemperature, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(hatcherTX.HatcherTempTargetIntTemperature, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(hatcherTX.HatcherTempTargetIntHumidity, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                hatcherRX.HatcherMode = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                hatcherRX.HatcherTempTargetExtTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherTempTargetIntTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherTempTargetIntHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherTargetExtTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherTargetIntTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherTargetIntHumidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherIntDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherIntDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherIntDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherExtDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherExtDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherExtDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherSCD30Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherSCD30Humidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.HatcherSCD30CO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                hatcherRX.SetterDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                pushData(client = client, timer=300, pushrx = hatcherRX)
                logging.info(msg = 'RX|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}'.format(
                    hatcherRX.HatcherMode,
                    hatcherRX.HatcherTempTargetExtTemperature,
                    hatcherRX.HatcherTempTargetIntTemperature,
                    hatcherRX.HatcherTempTargetIntHumidity,
                    hatcherRX.HatcherTargetExtTemperature,
                    hatcherRX.HatcherTargetIntTemperature,
                    hatcherRX.HatcherTargetIntHumidity,
                    hatcherRX.HatcherIntDSTempAverage,
                    hatcherRX.HatcherIntDSTemperature,
                    hatcherRX.HatcherIntDSErrorCount,
                    hatcherRX.HatcherExtDSTempAverage,
                    hatcherRX.HatcherExtDSTemperature,
                    hatcherRX.HatcherExtDSErrorCount,
                    hatcherRX.HatcherSCD30Temperature,
                    hatcherRX.HatcherSCD30Humidity,
                    hatcherRX.HatcherSCD30CO2,
                    hatcherRX.SetterDSTemperature
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