#!/usr/bin/env python3
import time
import datetime
from pySerialTransfer import pySerialTransfer as txfer
from tb_gateway_mqtt import TBDeviceMqttClient
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import pickle
import sys

pushTimer = time.time()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    HatcherMode = 0
    HatcherKp = 0.0
    HatcherKi = 0.0
    HatcherKd = 0.0
    HatcherTempWindow = 1000.0

def writeSettings(object_to_save):
    with open('HatcherSettings.ini', 'wb') as output:
        pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)
    logging.info("Settings saved")

def readSettings():
    with open('HatcherSettings.ini', 'rb') as input:
        p = pickle.load(input)
    return p

class structSettingsRX(object):
    HatcherMode = 0
    HatcherKp = 0.0
    HatcherKi = 0.0
    HatcherKd = 0.0
    HatcherMaxWindow = 0.0
    HatcherMinWindow = 0.0
    HatcherPIDWindow = 0.0
    HatcherWindow = 0.0
    HatcherIntDSTempAverage = 0.0
    HatcherIntDSTemperature = 0.0
    HatcherIntDSErrorCount = 0.0
    HatcherExtDSTempAverage = 0.0
    HatcherExtDSTemperature = 0.0
    HatcherExtDSErrorCount = 0.0
    HatcherSCD30Temperature = 0.0
    HatcherSCD30Humidity = 0.0
    HatcherSCD30CO2 = 0.0
    SetterDSTemperature = 0.0
    LastSerial = datetime.datetime.now()


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

def pushData(client, timer):
    global pushTimer
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "Hatcher Mode": structSettingsRX.HatcherMode,
                                      "Hatcher Kp": structSettingsRX.HatcherKp,
                                      "Hatcher Ki": structSettingsRX.HatcherKi,
                                      "Hatcher Kd": structSettingsRX.HatcherKd,
                                      "Hatcher Max Window":structSettingsRX.HatcherMaxWindow,
                                      "Hatcher Min Window": structSettingsRX.HatcherMinWindow,
                                      "Hatcher PID Window": structSettingsRX.HatcherPIDWindow,
                                      "Hatcher Window": structSettingsRX.HatcherWindow,
                                      "Hatcher Int Temperature Average": structSettingsRX.HatcherIntDSTempAverage,
                                      "Hatcher Int Temperature DS18": structSettingsRX.HatcherIntDSTemperature,
                                      "Hatcher Int DS18 Error count": structSettingsRX.HatcherIntDSErrorCount,
                                      "Hatcher Ext Temperature Average": structSettingsRX.HatcherExtDSTempAverage,
                                      "Hatcher Ext Temperature DS18": structSettingsRX.HatcherExtDSTemperature,
                                      "Hatcher Ext DS18 Error count": structSettingsRX.HatcherExtDSErrorCount,
                                      "Hatcher Temperature SCD30": structSettingsRX.HatcherSCD30Temperature,
                                      "Hatcher Humidity SCD30": structSettingsRX.HatcherSCD30Humidity,
                                      "Hatcher CO2 SCD30": structSettingsRX.HatcherSCD30CO2,
                                      "Setter Temperature DS18": structSettingsRX.SetterDSTemperature
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
    """Send a message when the command /start is issued."""
    datediff = datetime.datetime.now() - structSettingsRX.LastSerial
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your HATCHER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {structSettingsRX.LastSerial}')
    update.message.reply_text(fr'That was {round(datediff.total_seconds(), 0)} seconds ago')
    update.message.reply_text(fr'My temperature currently is {round(structSettingsRX.HatcherIntDSTempAverage,1)} °C')
    update.message.reply_text(fr'My humidity currently is {round(structSettingsRX.HatcherSCD30Humidity, 1)} %')

    update.message.reply_markdown_v2(
        fr'Thanks for asking {user.mention_markdown_v2()}\! Any other values wanted?',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text("No idea what you want from me")

def main():

    try:
        ## USB
        port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"  # replace 0 with whatever default you want
        host = sys.argv[2] if len(sys.argv) > 1 else "localhost"

        ## Thingsboard
        #client = TBDeviceMqttClient(host, "MetUfDYMrXno9RKiiGl7")
        client = TBDeviceMqttClient(host, "9aqkgXRwb56wOks7miIv")
        client.connect()
        client.subscribe_to_all_attributes(callback=callback)

        ## Serial communication
        link = txfer.SerialTransfer(port)
        link.open()
        time.sleep(2)

        ## Read last saved settings
        structSettingsTX = readSettings()

        ## Telegram
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater("5038308156:AAE7SJQUj2aA-3lXId-gWZnpHb1612gTKQw")

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("hatcher", hatcher))

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        # updater.idle()

        logging.info("Setup OK")
        while True:
            sendSize = 0
            sendSize = link.tx_obj(structSettingsTX.HatcherMode, start_pos=sendSize, val_type_override="B")
            sendSize = link.tx_obj(structSettingsTX.HatcherKp, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherKi, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherKd, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherMaxWindow, start_pos=sendSize, val_type_override="f")
            sendSize = link.tx_obj(structSettingsTX.HatcherMinWindow, start_pos=sendSize, val_type_override="f")
            link.send(sendSize)
            if link.available():
                recSize = 0
                logging.info("Starting RX")
                structSettingsRX.HatcherMode = link.rx_obj(obj_type='b', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['B']

                structSettingsRX.HatcherKp = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherKi = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherKd = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherMaxWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherMinWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherPIDWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherWindow = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherIntDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherIntDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherIntDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherExtDSTempAverage = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherExtDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherExtDSErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherSCD30Temperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherSCD30Humidity = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.HatcherSCD30CO2 = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.SetterDSTemperature = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.LastSerial = datetime.datetime.now()
                pushData(client = client, timer=300)
                logging.info(msg = 'RX | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} '.format(
                    structSettingsRX.HatcherMode,
                    structSettingsRX.HatcherKp,
                    structSettingsRX.HatcherKi,
                    structSettingsRX.HatcherKd,
                    structSettingsRX.HatcherMaxWindow,
                    structSettingsRX.HatcherMinWindow,
                    structSettingsRX.HatcherWindow,
                    structSettingsRX.HatcherIntDSTempAverage,
                    structSettingsRX.HatcherIntDSTemperature,
                    structSettingsRX.HatcherIntDSErrorCount,
                    structSettingsRX.HatcherExtDSTempAverage,
                    structSettingsRX.HatcherExtDSTemperature,
                    structSettingsRX.HatcherExtDSErrorCount,
                    structSettingsRX.HatcherSCD30Temperature,
                    structSettingsRX.HatcherSCD30Humidity,
                    structSettingsRX.HatcherSCD30CO2,
                    structSettingsRX.SetterDSTemperature
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