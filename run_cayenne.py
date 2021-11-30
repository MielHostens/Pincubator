#!/usr/bin/env python3
import time
import os
import cayenne.client
import serial
import simplejson as json


if __name__ == '__main__':

    # Cayenne authentication info. This should be obtained from the Cayenne Dashboard.
    MQTT_USERNAME = "8779fea0-1664-11e8-aeac-8375e928efd4"
    MQTT_PASSWORD = "27e17f1b8837423563c52bc22872efc0a2107548"
    MQTT_CLIENT_ID = "b9b7f620-49c8-11eb-8779-7d56e82df461"

    settings = {}

    TimeOnChannel = 0
    SetterOnOffChannel = 1
    HatcherOnOffChannel = 2
    PushOnOffChannel = 3
    SetterWindowChannel = 4
    HatcherWindowChannel = 5
    SetterDHTTemperatureChannel = 6
    SetterDHTHumidityChannel = 7
    SetterSCD30TemperatureChannel = 8
    SetterSCD30HumidityChannel = 9
    SetterSCD30CO2Channel = 10
    HatcherTemperatureChannel = 11
    HatcherHumidityChannel = 12
    HatcherCozirTemperatureChannel = 13
    HatcherCozirHumidityChannel = 14
    HatcherCozirCO2Channel = 15
    SetterPIDOnOffChannel = 16
    HatcherPIDOnOffChannel = 17
    SetterManualOnOffChannel = 18
    HatcherManualOnOffChannel = 19
    SetterKpChannel = 20
    SetterKiChannel = 21
    SetterKdChannel = 22
    HatcherKpChannel = 30
    HatcherKiChannel = 31
    HatcherKdChannel = 32
    SetterDS1TemperatureChannel = 40
    SetterDS2TemperatureChannel = 41
    HatcherExtDSTemperatureChannel = 42
    HatcherIntDSTemperatureChannel = 43


    # The callback for when a message is received from Cayenne.
    def on_message(message):
        #print("message received: " + str(message))
        switcher = {
            SetterOnOffChannel: updateSetterOnOff,
            HatcherOnOffChannel: updateHatcherOnOff,
            PushOnOffChannel: updatePushOnOff,
            SetterWindowChannel: updateSetterWindow,
            HatcherWindowChannel: updateHatcherWindow,
            SetterPIDOnOffChannel: updateSetterPIDOnOff,
            HatcherPIDOnOffChannel: updateHatcherPIDOnOff,
            SetterManualOnOffChannel: updateSetterManualOnOff,
            HatcherManualOnOffChannel: updateHatcherManualOnOff,
            SetterKpChannel: updateSetterKp,
            SetterKiChannel: updateSetterKi,
            SetterKdChannel: updateSetterKd,
            HatcherKpChannel: updateHatcherKp,
            HatcherKiChannel: updateHatcherKi,
            HatcherKdChannel: updateHatcherKd,
        }
        # Get the function from switcher dictionary
        func = switcher.get(message.channel, lambda: "Invalid month")
        # Execute the function
        func(message.value)

    def updateSetterOnOff(value):
        updateSettings("SetterOnOff", value)
    def updateSetterPIDOnOff(value):
        updateSettings("SetterPIDOnOff", value)
    def updatePushOnOff(value):
        updateSettings("PushOnOff", value)
    def updateSetterWindow(value):
        updateSettings("SetterWindow", value)
    def updateHatcherWindow(value):
        updateSettings("HatcherWindow", value)
    def updateHatcherOnOff(value):
        updateSettings("HatcherOnOff", value)
    def updateHatcherPIDOnOff(value):
        updateSettings("HatcherPIDOnOff", value)
    def updateSetterManualOnOff(value):
        updateSettings("SetterManualOnOff", value)
    def updateHatcherManualOnOff(value):
        updateSettings("HatcherManualOnOff", value)
    def updateSetterKp(value):
        updateSettings("SetterKp", value)
    def updateSetterKi(value):
        updateSettings("SetterKi", value)
    def updateSetterKd(value):
        updateSettings("SetterKd", value)
    def updateHatcherKp(value):
        updateSettings("HatcherKp", value)
    def updateHatcherKi(value):
        updateSettings("HatcherKi", value)
    def updateHatcherKd(value):
        updateSettings("HatcherKd", value)

    def updateSettings(key, value):
        global settings
        settings[key] = value
        print("Updated " + str(key) + " channel to value: " + str(value))
        writeSettings()

    def writeSettings():
        global settings
        with open('Setting.ini', 'w') as outfile:
            json.dump(settings, outfile)
        print("Settings saved")

    def readSettings():
        global settings
        with open('Setting.ini') as json_file:
            settings = json.load(json_file)

    def pushData(data_in):
        global settings
        client.virtualWrite(PushOnOffChannel, settings["PushOnOff"])
        client.virtualWrite(TimeOnChannel, data_in["TimeOn"])
        client.virtualWrite(SetterOnOffChannel, data_in["SetterOnOff"])
        client.virtualWrite(HatcherOnOffChannel, data_in["HatcherOnOff"])
        client.virtualWrite(SetterWindowChannel, data_in["SetterWindow"])
        client.virtualWrite(HatcherWindowChannel, data_in["HatcherWindow"])
        client.virtualWrite(SetterPIDOnOffChannel, data_in["SetterPIDOnOff"])
        client.virtualWrite(HatcherPIDOnOffChannel, data_in["HatcherPIDOnOff"])
        client.virtualWrite(SetterManualOnOffChannel, data_in["SetterManualOnOff"])
        client.virtualWrite(HatcherManualOnOffChannel, data_in["HatcherManualOnOff"])
        client.virtualWrite(SetterDHTTemperatureChannel, data_in["SetterDHTTempAverage"])
        client.virtualWrite(SetterDHTHumidityChannel, data_in["SetterDHTHumidity"])
        client.virtualWrite(SetterSCD30TemperatureChannel, data_in["SetterSCD30Temperature"])
        client.virtualWrite(SetterSCD30HumidityChannel, data_in["SetterSCD30Humidity"])
        client.virtualWrite(SetterSCD30CO2Channel, data_in["SetterSCD30CO2"])
        client.virtualWrite(SetterDS1TemperatureChannel, data_in["SetterDS1Temperature"])
        client.virtualWrite(SetterDS2TemperatureChannel, data_in["SetterDS2Temperature"])
        client.virtualWrite(HatcherTemperatureChannel, data_in["HatcherIntDHTTempAverage"])
        client.virtualWrite(HatcherHumidityChannel, data_in["HatcherIntDHTHumidity"])
        client.virtualWrite(HatcherCozirTemperatureChannel, data_in["HatcherCozirTemperature"])
        client.virtualWrite(HatcherCozirHumidityChannel, data_in["HatcherCozirHumidity"])
        client.virtualWrite(HatcherCozirCO2Channel, data_in["HatcherCozirCO2"])
        client.virtualWrite(HatcherIntDSTemperatureChannel, data_in["HatcherIntDSTemperature"])
        client.virtualWrite(SetterKpChannel, data_in["SetterKp"])
        client.virtualWrite(SetterKiChannel, data_in["SetterKi"])
        client.virtualWrite(SetterKdChannel, data_in["SetterKp"])
        client.virtualWrite(HatcherKpChannel, data_in["HatcherKp"])
        client.virtualWrite(HatcherKiChannel, data_in["HatcherKi"])
        client.virtualWrite(HatcherKdChannel, data_in["HatcherKd"])

    def checkSetter(data, interval):
        global setterCheckTime
        if abs(time.time() - setterCheckTime) > interval:
            print("Checking Setter")
            if "SetterTempAverage" in data:
                if float(data["SetterTempAverage"]) < 36.0:
                    alert_message("Setter TEMPERATURE is too low: "  +  data["SetterTempAverage"])
                    print("Alert message sent")
            if "SetterTempAverage" in data:
                if float(data["SetterTempAverage"]) > 38.5:
                    alert_message("Setter TEMPERATURE too high: "  +  data["SetterTempAverage"])
                    print("Alert message sent")
            if "SetterHumidity" in data:
                if float(data["SetterHumidity"]) < 10.0:
                    alert_message("Setter HUMIDITY is too low: "  +  data["SetterHumidity"])
                    print("Alert message sent")
            if "SetterCozirCO2" in data:
                if float(data["SetterCozirCO2"]) > 5000.0:
                    alert_message("Setter CO2 is too High: " + data["SetterCozirCO2"])
                    print("Alert message sent")
            setterCheckTime = time.time()

    def checkHatcher(data, interval):
        global hatcherCheckTime
        if abs(time.time() - hatcherCheckTime) > interval:
            print("Checking Hatcher")
            if "HatcherIntTempAverage" in data:
                if float(data["HatcherIntTempAverage"]) < 36.0:
                    alert_message("Hatcher TEMPERATURE is too low: "  +  data["HatcherIntTempAverage"])
                    print("Alert message sent")
            if "HatcherIntTempAverage" in data:
                if float(data["HatcherIntTempAverage"]) > 38.5:
                    alert_message("Hatcher TEMPERATURE too high: "  +  data["HatcherIntTempAverage"])
                    print("Alert message sent")
            if "HatcherIntHumidity" in data:
                if float(data["HatcherIntHumidity"]) < 10.0:
                    alert_message("Hatcher HUMIDITY is too low: "  +  data["HatcherIntHumidity"])
                    print("Alert message sent")
            if "HatcherCozirCO2" in  data:
                if float(data["HatcherCozirCO2"]) > 5000.0:
                    alert_message("Hatcher CO2 is too High: " + data["HatcherCozirCO2"])
                    print("Alert message sent")
            hatcherCheckTime = time.time()

    #Timers
    setterCheckTime = time.time()
    hatcherCheckTime = time.time()

    # Initiate Cayenne
    client = cayenne.client.CayenneMQTTClient()
    client.on_message = on_message
    client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)

    # Start serial port
    # ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    # ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser = serial.Serial('COM7')
    # ser.reset_input_buffer()
    ser.flush()
    buffer = ""

    # Read settings from Settings.ini
    readSettings()

    #Finish by sending message
    start_message()

    while True:
        try:

            data_out_json = json.dumps(settings)
            ser.write(data_out_json.encode('ascii'))
            ser.flush()
            buffer = ser.readline()
            print(buffer)
            if buffer != b'':
                data_incubator = json.loads(buffer)
                pushData(data_incubator)
                if int(settings["PushOnOff"]) == 199:
                    print("Push notifications Off")
                else:
                    print("Push notifications On")
                    interval = int(settings["PushOnOff"])
                    if int(settings["SetterOnOff"]) == 1:
                        print("Checking setter")
                        checkSetter(data_incubator, interval*60)
                    if int(settings["HatcherOnOff"]) == 1:
                        print("Checking hatcher")
                        checkHatcher(data_incubator, interval*60)
                client.loop()
        except json.JSONDecodeError:
            print("Error : try to parse an incomplete message")
        time.sleep(10)