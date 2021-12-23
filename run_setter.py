#!/usr/bin/env python3
from pySerialTransfer import pySerialTransfer as txfer
from tb_gateway_mqtt import TBDeviceMqttClient
import sys, json, codecs, os, time, logging, pickle, datetime
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

pushTimer = time.time()
LastSerial = datetime.datetime.now()
AlarmTimer = time.time()
Alarm = 0

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class structSettingsTX(object):
    def __init__(self):
        self.SetterMode = 3  # an instance attribute
        self.SetterKp = 750.0  # an instance attribute
        self.SetterKi = 0.0  # an instance attribute
        self.SetterKd = 0.0  # an instance attribute
        self.SetterMaxWindow = 2000.0  # an instance attribute
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
    global Alarm
    if key.__contains__("Alarm"):
        Alarm = value
        logging.info("Alarm mode changed")
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
        p = pickle.load(input)
    return p

def telegramAlarm(update, timer, pushrx)-> None:
    global AlarmTimer
    global Alarm
    if (time.time() - AlarmTimer > timer):
        AlarmTimer = time.time()
        if Alarm == 1:
            if pushrx.SetterTemperatureAverage < 36.0:
                update.message.reply_text("Setter temperature < 36.0°C")
            elif pushrx.SetterTemperatureAverage > 38.5:
                update.message.reply_text("Setter temperature > 38.5°C")
            if pushrx.HatcherDS1Temperature < 36.0:
                update.message.reply_text("Hatcher temperature < 36.0°C")
            elif pushrx.HatcherDS1Temperature > 38.5:
                update.message.reply_text("Hatcher temperature > 38.5°C")

def pushData(client, timer, pushrx):
    global pushTimer
    if (time.time() - pushTimer > timer):
        pushTimer = time.time()
        client.request_attributes()
        client.send_telemetry(
                                {"ts": int(round(time.time() * 1000)),
                                  "values": {
                                      "Setter Mode": pushrx.SetterMode,
                                      "Setter Max Window":pushrx.SetterMaxWindow,
                                      "Setter Min Window": pushrx.SetterMinWindow,
                                      "Setter PID Window": pushrx.SetterPIDWindow,
                                      "Setter Window": pushrx.SetterWindow,
                                      "Setter Temperature Average": pushrx.SetterTemperatureAverage,
                                      "Setter Temperature DHT22": pushrx.SetterDHTTemperature,
                                      "Setter Humidity DHT22": pushrx.SetterDHTHumidity,
                                      "Setter Temperature SCD30": pushrx.SetterSCD30Temperature,
                                      "Setter Humidity SCD30": pushrx.SetterSCD30Humidity,
                                      "Setter CO2 SCD30": pushrx.SetterSCD30CO2,
                                      "Setter Temperature DS18 1": pushrx.SetterDS1Temperature,
                                      "Setter Temperature DS18 2": pushrx.SetterDS2Temperature,
                                      "Setter Kp": pushrx.SetterKp,
                                      "Setter Ki": pushrx.SetterKi,
                                      "Setter Kd": pushrx.SetterKd,
                                      "Setter Error Count": pushrx.SetterErrorCount,
                                      "Hatcher Temperature DS18 Extra": pushrx.HatcherDS1Temperature
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
    global setterRX
    global LastSerial
    """Send a message when the command /start is issued."""
    datediff = datetime.datetime.now() - LastSerial
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your SETTER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {LastSerial}')
    update.message.reply_text(fr'That was {round(datediff.total_seconds(), 0)} seconds ago')
    update.message.reply_text(fr'My temperature currently is {round(setterRX.SetterTemperatureAverage,1)} °C')
    update.message.reply_text(fr'My humidity currently is {round(setterRX.SetterSCD30Humidity, 1)} %')
    update.message.reply_markdown_v2(
        fr'Thanks for asking {user.mention_markdown_v2()}\! Anything else wanted?',
        reply_markup=ForceReply(selective=True),
    )

def hatcher(update: Update, context: CallbackContext) -> None:
    global setterRX
    global LastSerial
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(fr'Hi {user.first_name}, this is your SETTER replying')
    update.message.reply_text(fr'My last serial communication with arduino was at {LastSerial}')
    update.message.reply_text(fr'The HATCHER temperature currently is {round(setterRX.HatcherDS1Temperature, 1)} °C')
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

    global setterRX
    global setterTX
    global LastSerial

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
            # Check for alarm and set
            telegramAlarm(update=updater, timer=300, pushrx=setterRX)
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

                logging.info(msg = 'RX'
                                   'Setter Mode {}'
                                   '|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}'.format(
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
                pushData(client = client, timer=300, pushrx = setterRX)
                LastSerial = datetime.datetime.now()

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