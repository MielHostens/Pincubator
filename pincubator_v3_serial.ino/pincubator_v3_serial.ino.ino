#include "DHT.h"
#include "cozir.h"
#include "SoftwareSerial.h"
#include "PID_v1.h"
#include "ArduinoJson.h"

#define VCSetterOnOff 1
#define VCHatcherOnOff 2
//#define VCPushNotifications 3
#define VCSetterPIDOnOff 4
#define VCHatcherPIDOnOff 5
#define VCSetterKp 20
#define VCSetterKi 21
#define VCSetterKd 22
#define VCHatcherKp 30
#define VCHatcherKi 31
#define VCHatcherKd 32


// ************************************************
// Pin definitions & sensors
// ************************************************

// Constants for Arduino relay board
#define RelayON 0
#define RelayOFF 1

//Constants for DHT sensors
#define DHTType DHT22   // DHT 22  (AM2302)
#define SetterPinDHT 2     // what pin is connected to the outside temperature room (OUT)
#define HatcherPinIntDHT 3     // what pin is connected to the inside temperature room (IN)
#define HatcherPinExtDHT 4

//Constants for Arduino relay board switches
#define PinRelayUnused6 6
#define PinRelayUnused7 7
#define HatcherPinRelayHumidity 8
#define SetterPinRelayEggTurner 9

//Cozir pins
//Hatcher
#define HatcherPinCozir1 10
#define HatcherPinCozir2 11
//Setter
//#define PinSetterCozir1
//#define PinSetterCozir2

//SSR pins
#define SetterPinSSRTemperature 12
#define HatcherPinSSRTemperature 13

//SSR
#define BlinkerPin 53

DHT SetterDHT(SetterPinDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino
DHT HatcherIntDHT(HatcherPinIntDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino
DHT HatcherExtDHT(HatcherPinExtDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino

//Variables
double HatcherIntHumidity;  //Stores internal humidity value
double HatcherIntTemperature; //Stores internal temperature value
double HatcherExtTemperature; //Stores external temperature value
double SetterHumidity;  //Stores internal humidity value
double SetterTemperature; //Stores internal temperature value

//Cozir
double HatcherCozirTemperature;
double HatcherCozirHumidity;
int HatcherCozirCO2;

double SetterCozirTemperature;
double SetterCozirHumidity;
int SetterCozirCO2;

//Hatcher goals
double HatcherTargetExtTemperature = 40.1;  //Setting external temperature value
double HatcherTargetIntTemperature = 37.6;
double HatcherTargetIntHumidity = 65.0; //Stores internal temperature value

//Setter goals
double SetterTargetTemperature = 37.8;
double SetterTargetHumidity = 45.0;

//CO2 goals
int SetterTargetCO2 = 5000; //Max ppm
int HatcherTargetCO2 = 5000;

//Keeping track of number of erroneous readings
long SetterDHTErrorCount = 0;
long HatcherExtDHTErrorCount = 0;
long HatcherIntDHTErrorCount = 0;

//DHT Smoothing
// Define the number of samples to keep track of. The higher the number, the
// more the readings will be smoothed, but the slower the output will respond to
// the input. Using a constant rather than a normal variable lets us use this
// value to determine the size of the readings array.
const int numReadings = 60;
double SetterReadings[numReadings];      // the readings from the analog input
int SetterTempReadIndex = 0;              // the index of the current reading
double SetterTempTotal = 0.0;                  // the running total
double SetterTempAverage = 0.0;                // the average

double HatcherExtReadings[numReadings];      // the readings from the analog input
int HatcherExtTempReadIndex = 0;              // the index of the current reading
double HatcherExtTempTotal = 0.0;                  // the running total
double HatcherExtTempAverage = 0;                // the average

double HatcherIntReadings[numReadings];      // the readings from the analog input
int HatcherIntTempReadIndex = 0;              // the index of the current reading
double HatcherIntTempTotal = 0.0;                  // the running total
double HatcherIntTempAverage = 0.0;                // the average

//Specifiy window sizes for sensors
unsigned long LastSerialPush = 0;
unsigned long SetterLastSensorCheck = 0;
unsigned long SetterLastEggTurnCheck = 0;
unsigned long SetterLastTemperatureTargetCheck = 0;
unsigned long SetterLastCozirCheck = 0;
unsigned long SetterWindowLastCheck = 0;

unsigned long HatcherLastOnOffCheck = 0;
unsigned long HatcherLastSensorCheck = 0;
unsigned long HatcherLastTemperatureTargetCheck = 0;
unsigned long HatcherLastCozirCheck = 0;
unsigned long  HatcherWindowLastCheck = 0;

unsigned long BlinkerLastCheck = 0;
int ledState = LOW;

//Initialize COZIR
SoftwareSerial Hatchersws(HatcherPinCozir1, HatcherPinCozir2);
COZIR Hatcherczr(&Hatchersws);

//Initialize COZIR
//SoftwareSerial swsSetter(PinSetterCozir1, PinSetterCozir2);
//COZIR Setterczr(&swsSetter);

// **************************************************************
// * VIRTUAL SWITCHES
// ***************************************************************/
byte SimulatorOnOff = 1;

byte SetterOnOff = 1;
byte SetterManualOnOff = 1;
byte SetterPIDOnOff = 0;

byte HatcherOnOff = 0;
byte HatcherManualOnOff = 0;
byte HatcherPIDOnOff = 0;

// ************************************************
// PID Variables and constants
// ************************************************

//Define Variables we'll be connecting to
double  SetterKp = 0.1;
double  SetterKi = 3.0;
double  SetterKd = 0.2;
double  SetterWindow = 1000;
double  SetterTempWindow = 1000;

double  HatcherKp = 0.1;
double  HatcherKi = 3.0;
double  HatcherKd = 0.2;
double  HatcherWindow = 1000;
double  HatcherTempWindow = 1000;

//Specify the links and initial tuning parameters
PID mySetterPID(&SetterTempAverage, &SetterWindow, &SetterTargetTemperature, SetterKp, SetterKi, SetterKd, DIRECT);
PID myHatcherPID(&HatcherIntTempAverage, &HatcherWindow, &HatcherTargetIntTemperature, HatcherKp, HatcherKi, HatcherKd, DIRECT);

StaticJsonDocument<512> InDoc;
StaticJsonDocument<512> OutDoc;

void setup()
{

  // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);

  // **************************************************************
  // * PINS
  // ***************************************************************/
  // Set pins as outputs
  pinMode(PinRelayUnused6, OUTPUT);
  pinMode(PinRelayUnused7, OUTPUT);
  pinMode(HatcherPinRelayHumidity, OUTPUT);
  pinMode(SetterPinRelayEggTurner, OUTPUT);
  pinMode(SetterPinSSRTemperature, OUTPUT);
  pinMode(HatcherPinSSRTemperature, OUTPUT);
  pinMode(BlinkerPin, OUTPUT);

  // Initialize Pins so relays are inactive at reset
  digitalWrite(PinRelayUnused6, RelayOFF);
  digitalWrite(PinRelayUnused7, RelayOFF);
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(SetterPinRelayEggTurner, RelayOFF);
  digitalWrite(SetterPinSSRTemperature, LOW);
  digitalWrite(HatcherPinSSRTemperature, LOW);
  digitalWrite(BlinkerPin, LOW);

  // **************************************************************
  // * START SENSORS
  // ***************************************************************/
  // Turn DHT sensors on
  SetterDHT.begin();
  HatcherIntDHT.begin();
  HatcherIntDHT.begin();


  // **************************************************************
  // * PID
  // ***************************************************************/
  mySetterPID.SetMode(AUTOMATIC);
  mySetterPID.SetOutputLimits(300, 1000);
  myHatcherPID.SetMode(AUTOMATIC);
  myHatcherPID.SetOutputLimits(300, 1000);
  //myPID.SetSampleTime(60000);

  // **************************************************************
  // * SMOOTHERS
  // ***************************************************************/
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    SetterReadings[thisReading] = 0.0;
  }
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherExtReadings[thisReading] = 0.0;
  }
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherIntReadings[thisReading] = 0.0;
  }

  // **************************************************************
  // * SETUP FINISHED
  // ***************************************************************/

  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  digitalWrite(PinRelayUnused6, RelayON);
  delay(1000);
  digitalWrite(PinRelayUnused6, RelayOFF);
}

void loop() {
  if (SimulatorOnOff == 1) SensorSimulator();
  if (SetterOnOff == 0) SetterOff(); else SetterOn();
  if (HatcherOnOff == 0) HatcherOff(); else HatcherOn();
  SerialSendReceive(1000);
  ToggleBlink(500);

}
void SensorSimulator() {
  SetterTempAverage = random(370, 380) / 10.0;
  SetterHumidity = random(400, 500) / 10.0;
  SetterCozirTemperature = random(370, 380) / 10.0;
  SetterCozirHumidity = random(400, 500) / 10.0;
  SetterCozirCO2 = random(2700, 2800);
  HatcherIntTempAverage = random(370, 380) / 10.0;
  HatcherIntHumidity = random(550, 650) / 10.0;
  HatcherCozirTemperature = random(370, 380) / 10.0;
  HatcherCozirHumidity = random(550, 650) / 10.0;
  HatcherCozirCO2 = random(2700, 2800);
}
void SerialSendReceive(int interval) {
  //Read all sensors in the setter
  if (millis() - LastSerialPush >= interval)
  {
    LastSerialPush = millis();
    if (Serial.available() > 0) {
      String payload = Serial.readStringUntil( '\n' );
      DeserializationError error = deserializeJson(InDoc, payload);
      if (error) {
        //Serial.println(error.c_str());
        //return;
      }
      else {
        SetterOnOff = InDoc["SetterOnOff"].as<unsigned long>();
        HatcherOnOff = InDoc["HatcherOnOff"].as<unsigned long>();
        SetterManualOnOff = InDoc["SetterManualOnOff"].as<unsigned long>();
        HatcherManualOnOff = InDoc["HatcherManualOnOff"].as<unsigned long>();
        SetterTempWindow = InDoc["SetterWindow"].as<double>();
        HatcherTempWindow = InDoc["HatcherWindow"].as<double>();
        SetterPIDOnOff = InDoc["SetterPIDOnOff"].as<unsigned long>();
        HatcherPIDOnOff = InDoc["HatcherPIDOnOff"].as<unsigned long>();
        SetterKp = InDoc["SetterKp"].as<double>();
        SetterKi = InDoc["SetterKi"].as<double>();
        SetterKd = InDoc["SetterKd"].as<double>();
        HatcherKp = InDoc["HatcherKp"].as<double>();
        HatcherKi = InDoc["HatcherKi"].as<double>();
        HatcherKd = InDoc["HatcherKd"].as<double>();

        //Send v2
        OutDoc["TimeOn"] = String(millis() / 1000);
        OutDoc["SetterOnOff"] = String(SetterOnOff);
        OutDoc["HatcherOnOff"] = String(HatcherOnOff);
        OutDoc["SetterWindow"] = String(SetterWindow);
        OutDoc["HatcherWindow"] = String(HatcherWindow);
        OutDoc["SetterPIDOnOff"] = String(SetterPIDOnOff);
        OutDoc["HatcherPIDOnOff"] = String(HatcherPIDOnOff);
        OutDoc["SetterManualOnOff"] = String(SetterManualOnOff);
        OutDoc["HatcherManualOnOff"] = String(HatcherManualOnOff);
        OutDoc["SetterTempAverage"] = String(SetterTempAverage);
        OutDoc["SetterHumidity"] = String(SetterHumidity);
        OutDoc["SetterCozirTemperature"] = String(SetterCozirTemperature);
        OutDoc["SetterCozirHumidity"] = String(SetterCozirHumidity);
        OutDoc["SetterCozirCO2"] = String(SetterCozirCO2);
        OutDoc["HatcherIntTempAverage"] = String(HatcherIntTempAverage);
        OutDoc["HatcherIntHumidity"] = String(HatcherIntHumidity);
        OutDoc["HatcherCozirTemperature"] = String(HatcherCozirTemperature);
        OutDoc["HatcherCozirHumidity"] = String(HatcherCozirHumidity);
        OutDoc["HatcherCozirCO2"] = String(HatcherCozirCO2);
        OutDoc["SetterKp"] = String(SetterKp);
        OutDoc["SetterKi"] = String(SetterKi);
        OutDoc["SetterKd"] = String(SetterKd);
        OutDoc["HatcherKp"] = String(HatcherKp);
        OutDoc["HatcherKi"] = String(HatcherKi);
        OutDoc["HatcherKd"] = String(HatcherKd);
        serializeJson(OutDoc, Serial);
      }
    }
  }
}
void SetterOn() {
  //SimulatorOnOff == 0;
  //SetterReadSensors(10000); // every 10 seconds
  SetterEggTurn(3600000); //every hour
  if (SetterManualOnOff == 1) SetterManualMode();
  else {
    if (SetterPIDOnOff == 0) SetterAutomaticMode(60000, false);
    else SetterAutomaticMode(60000, true);
  }
  SetterPWM(10000);
}
void SetterOff() {
  SimulatorOnOff == 1;
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(SetterPinSSRTemperature, LOW);
}
void SetterReadSensors(int interval) {
  //Read all sensors in the setter
  if (millis() - SetterLastSensorCheck >= interval)
  {
    SetterLastSensorCheck = millis(); //reset timer
    if (isnan(SetterDHT.readTemperature()) ||
        SetterDHT.readTemperature() < 10.0 ||
        abs(SetterDHT.readTemperature() - SetterReadings[SetterTempReadIndex]) > 10.0)
    {
      SetterDHTErrorCount += 1;
    }
    else
    {
      SetterHumidity = SetterDHT.readHumidity();
      SetterTemperature = SetterDHT.readTemperature();
      // Smoothing algorythm
      // subtract the last reading:
      SetterTempTotal = SetterTempTotal - SetterReadings[SetterTempReadIndex];
      // read from the sensor:
      SetterReadings[SetterTempReadIndex] = SetterTemperature;
      // add the reading to the total:
      SetterTempTotal = SetterTempTotal + SetterReadings[SetterTempReadIndex];
      // advance to the next position in the array:
      SetterTempReadIndex = SetterTempReadIndex + 1;

      // if we're at the end of the array...
      if (SetterTempReadIndex >= numReadings) {
        // ...wrap around to the beginning:
        SetterTempReadIndex = 0;
      }
      // calculate the average:
      SetterTempAverage = SetterTempTotal / numReadings;
      // send it to the computer as ASCII digits
    }

  }
}
void SetterEggTurn(int interval) {
  /************************************************
    SETTER TURNING
  ************************************************/
  if (millis() - SetterLastEggTurnCheck >= interval)
  {
    SetterLastEggTurnCheck = millis();
    digitalWrite(SetterPinRelayEggTurner, RelayON);
    delay(12000); //2.5 rpm at 50 Hz -> 12 sec for half turn
    digitalWrite(SetterPinRelayEggTurner, RelayOFF);
  }
}
void SetterManualMode() {
  SetterWindow = SetterTempWindow;
}
void SetterAutomaticMode(int interval, bool PID) {
  //Compute output with or without PID
  if (millis() - SetterLastTemperatureTargetCheck >= interval)
  { //time to shift the Relay Window
    SetterLastTemperatureTargetCheck = millis();
    if (PID) {
      SetterPIDAdjustTemperatureTarget();
    }
    else {
      SetterStepAdjustTemperatureTarget();
    }
  }
}
void SetterPIDAdjustTemperatureTarget() {
  mySetterPID.SetTunings(SetterKp, SetterKi, SetterKd);
  mySetterPID.Compute();
}
void SetterStepAdjustTemperatureTarget() {
  if ((SetterTempAverage > (SetterTargetTemperature + 0.15)) && SetterWindow > 300.0)
  {
    SetterWindow -= 20.0;
  }
  else if ((SetterTempAverage > (SetterTargetTemperature + 0.1)) && SetterWindow > 300.0)
  {
    SetterWindow -= 10.0;
  }
  else if (SetterTempAverage < (SetterTargetTemperature - 0.2) && SetterWindow < 700.0)
  {
    SetterWindow += 10.0;
  }
  else if (SetterTempAverage < (SetterTargetTemperature - 0.1) && SetterWindow < 700.0)
  {
    SetterWindow += 5.0;
  }
}
void SetterPWM(int interval) {
  if (millis() - SetterWindowLastCheck >= interval)
  { //time to shift the Relay Window
    SetterWindowLastCheck += interval;
  }
  if (SetterWindow > millis() - SetterWindowLastCheck) digitalWrite(SetterPinSSRTemperature, HIGH);
  else digitalWrite(SetterPinSSRTemperature, LOW);
}
void HatcherOn() {
  HatcherReadSensors(10000);
  HatcherTemperatureCheck();
  HatcherHumidityCheck();
  HatcherStepAdjustTemperatureTarget();
  HatcherPWM(10000);
}
void HatcherOff() {
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(HatcherPinSSRTemperature, LOW);
}
void HatcherReadSensors(int interval) {
  //Read all sensors in the setter
  if (millis() - HatcherLastSensorCheck >= interval)
  {
    HatcherLastSensorCheck = millis(); //reset timer
    if (isnan(HatcherIntDHT.readTemperature()) ||  HatcherIntDHT.readTemperature() < 10.0 || abs(HatcherIntDHT.readTemperature() - HatcherIntReadings[HatcherIntTempReadIndex]) > 10.0)
    {
      HatcherIntDHTErrorCount += 1;
      return;
    }
    else
    {
      HatcherIntHumidity = HatcherIntDHT.readHumidity();
      HatcherIntTemperature = HatcherIntDHT.readTemperature();
      // Smoothing algorythm
      // subtract the last reading:
      HatcherIntTempTotal = HatcherIntTempTotal - HatcherIntReadings[HatcherIntTempReadIndex];
      // read from the sensor:
      HatcherIntReadings[HatcherIntTempReadIndex] = HatcherIntTemperature;
      // add the reading to the total:
      HatcherIntTempTotal = HatcherIntTempTotal + HatcherIntReadings[HatcherIntTempReadIndex];
      // advance to the next position in the array:
      HatcherIntTempReadIndex = HatcherIntTempReadIndex + 1;

      // if we're at the end of the array...
      if (HatcherIntTempReadIndex >= numReadings) {
        // ...wrap around to the beginning:
        HatcherIntTempReadIndex = 0;
      }
      // calculate the average:
      HatcherIntTempAverage = HatcherIntTempTotal / numReadings;
      // send it to the computer as ASCII digits
    }

    if (isnan(HatcherExtDHT.readTemperature()) || HatcherExtDHT.readTemperature() < 10.0 || abs(HatcherExtDHT.readTemperature() - HatcherExtReadings[HatcherExtTempReadIndex]) > 10.0)
    {
      HatcherExtDHTErrorCount += 1;
      return;
    }
    else
    {
      HatcherExtTemperature = HatcherExtDHT.readTemperature();
      // Smoothing algorythm
      // subtract the last reading:
      HatcherExtTempTotal = HatcherExtTempTotal - HatcherExtReadings[HatcherExtTempReadIndex];
      // read from the sensor:
      HatcherExtReadings[HatcherExtTempReadIndex] = HatcherExtTemperature;
      // add the reading to the total:
      HatcherExtTempTotal = HatcherExtTempTotal + HatcherExtReadings[HatcherExtTempReadIndex];
      // advance to the next position in the array:
      HatcherExtTempReadIndex = HatcherExtTempReadIndex + 1;

      // if we're at the end of the array...
      if (HatcherExtTempReadIndex >= numReadings) {
        // ...wrap around to the beginning:
        HatcherExtTempReadIndex = 0;
      }
      // calculate the average:
      HatcherExtTempAverage = HatcherExtTempTotal / numReadings;
      // send it to the computer as ASCII digits
    }

    //CO2 Sensors
    HatcherCozirTemperature = Hatcherczr.Celsius();
    HatcherCozirHumidity = Hatcherczr.Humidity();
    HatcherCozirCO2 = Hatcherczr.CO2();
  }
}
void HatcherManualMode() {
  HatcherWindow = HatcherTempWindow;
}
void HatcherTemperatureCheck() {
  //HATCHER TEMPERATURE CHECK
  if (HatcherExtTemperature > HatcherTargetExtTemperature + 0.2) digitalWrite(HatcherPinSSRTemperature, LOW);
  else if (HatcherExtTemperature < HatcherTargetExtTemperature - 0.2) digitalWrite(HatcherPinSSRTemperature, HIGH);
}
void HatcherHumidityCheck() {
  //SET HATCHER HUMIDITY
  if (HatcherIntHumidity > HatcherTargetIntHumidity + 5.0) digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  else if (HatcherIntHumidity < HatcherTargetIntHumidity - 5.0) digitalWrite(HatcherPinRelayHumidity, RelayON);
}
void HatcherAutomaticMode(int interval, bool PID) {
  //Compute output with or without PID
  if (millis() - HatcherLastTemperatureTargetCheck >= interval)
  { //time to shift the Relay Window
    HatcherLastTemperatureTargetCheck = millis();
    if (PID) {
      HatcherPIDAdjustTemperatureTarget();
    }
    else {
      HatcherStepAdjustTemperatureTarget();
    }
  }
}
void HatcherPIDAdjustTemperatureTarget() {
  myHatcherPID.SetTunings(HatcherKp, HatcherKi, HatcherKd);
  myHatcherPID.Compute();
}
void HatcherStepAdjustTemperatureTarget() {
  /************************************************
    HATCHER SETPOINT ADJUSTMENT
  ************************************************/
  if (millis() - HatcherLastTemperatureTargetCheck >= 900000)
  { //time to shift the temperature set 0.2 down or 0.1 up each 15 minutes
    HatcherLastTemperatureTargetCheck =  millis();
    if (HatcherIntTemperature > HatcherTargetIntTemperature + 0.3) HatcherTargetExtTemperature -= 0.5;
    else if (HatcherIntTemperature < HatcherTargetIntTemperature - 0.3) HatcherTargetExtTemperature += 0.1;
  }
}
void HatcherPWM(int interval) {
  //Turn the output pin on/off based on pid output
  //Pot value to adjust the sensor settings
  if (millis() - HatcherWindowLastCheck >= interval)
  { //time to shift the Relay Window
    HatcherWindowLastCheck += interval;
  }
  if (HatcherWindow > millis() - HatcherWindowLastCheck) digitalWrite(HatcherPinSSRTemperature, HIGH);
  else digitalWrite(HatcherPinSSRTemperature, LOW);
}

void ToggleBlink(long interval) {
  //Watch out, number 13 pin is LED_BUILTIN
  if (millis() - BlinkerLastCheck >= interval) {
    // save the last time you blinked the LED
    BlinkerLastCheck = millis();
    // if the LED is off turn it on and vice-versa:
    if (ledState == LOW) {
      ledState = HIGH;
    } else {
      ledState = LOW;
    }
    // set the LED with the ledState of the variable:
    digitalWrite(BlinkerPin, ledState);
  }
}
