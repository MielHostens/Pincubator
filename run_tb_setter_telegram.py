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
    SetterMode = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    SetterTempWindow = 1000.0

def writeSettings(object_to_save):
    with open('SetterSettings.ini', 'wb') as output:
        pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)
    logging.info("Settings saved")

def readSettings():
    with open('SetterSettings.ini', 'rb') as input:
        p = pickle.load(input)
    return p

class structSettingsRX(object):
    SetterMode = 0
    SetterKp = 0.0
    SetterKi = 0.0
    SetterKd = 0.0
    SetterMaxWindow = 0.0
    SetterMinWindow = 0.0
    SetterPIDWindow = 0.0
    SetterWindow = 0.0
    SetterDHTTemperatureAverage = 0.0
    SetterDHTTemperature = 0.0
    SetterDHTHumidity = 0.0
    SetterSCD30Temperature = 0.0
    SetterSCD30Humidity = 0.0
    SetterSCD30CO2 = 0.0
    SetterDS1Temperature = 0.0
    SetterDS2Temperature = 0.0
    SetterDHTErrorCount = 0.0
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
                                      "Setter Mode": structSettingsRX.SetterMode,
                                      "Setter Max Window":structSettingsRX.SetterMaxWindow,
                                      "Setter Min Window": structSettingsRX.SetterMinWindow,
                                      "Setter PID Window": structSettingsRX.SetterPIDWindow,
                                      "Setter Window": structSettingsRX.SetterWindow,
                                      "Setter Temperature Average": structSettingsRX.SetterDHTTemperatureAverage,
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
                                      "Setter Error Count": structSettingsRX.SetterDHTErrorCount
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

def setter(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    datediff = datetime.datetime.now() - structSettingsRX.LastSerial
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your SETTER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {structSettingsRX.LastSerial}')
    update.message.reply_text(fr'That was {round(datediff.total_seconds(), 0)} seconds ago')
    update.message.reply_text(fr'My temperature currently is {round(structSettingsRX.SetterDHTTemperature,1)} °C')
    update.message.reply_text(fr'My humidity currently is {round(structSettingsRX.SetterDHTHumidity, 1)} %')

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
        dispatcher.add_handler(CommandHandler("setter", setter))

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

                structSettingsRX.SetterDHTTemperatureAverage = link.rx_obj(obj_type='f', start_pos=recSize)
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

                structSettingsRX.SetterDHTErrorCount = link.rx_obj(obj_type='f', start_pos=recSize)
                recSize += txfer.STRUCT_FORMAT_LENGTHS['f']

                structSettingsRX.LastSerial = datetime.datetime.now()
                pushData(client = client, timer=300)
                logging.info(msg = 'RX | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} '.format(
                    structSettingsRX.SetterMode,
                    structSettingsRX.SetterKp,
                    structSettingsRX.SetterKi,
                    structSettingsRX.SetterKd,
                    structSettingsRX.SetterMaxWindow,
                    structSettingsRX.SetterWindow,
                    structSettingsRX.SetterDHTTemperatureAverage,
                    structSettingsRX.SetterDHTTemperature,
                    structSettingsRX.SetterDHTHumidity,
                    structSettingsRX.SetterSCD30Temperature,
                    structSettingsRX.SetterSCD30Humidity,
                    structSettingsRX.SetterSCD30CO2,
                    structSettingsRX.SetterDS1Temperature,
                    structSettingsRX.SetterDS2Temperature,
                    structSettingsRX.SetterDHTErrorCount
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