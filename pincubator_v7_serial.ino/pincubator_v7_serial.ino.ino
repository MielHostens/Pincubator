#include "DHT.h"
#include "cozir.h"
#include "SoftwareSerial.h"
#include "PID_v1.h"
#include "OneWire.h"
#include "DallasTemperature.h"
#include "Adafruit_SCD30.h"
#include "SerialTransfer.h"

// ************************************************
// Pin definitions & sensors
// ************************************************
#define HatcherPinIntDHT 3     // Pin for DHT hatcher
#define PinRelayUnused6 6 // Unused relay
#define PinRelayUnused7 7 // Unused relay
#define HatcherPinRelayHumidity 8 // Pin for relay for humidity in hatcher
#define SetterPinRelayEggTurner 9 // Pin for relay for egg turner in setter 
#define HatcherPinCozir1 10 // COZIR Serial pin 1
#define HatcherPinCozir2 11 // COZIR Serial pin 2
#define SetterPinSSRTemperature 12 //SSR Setter pin
//#define HatcherPinSSRTemperature 39 //SST Hatcher pin
#define HatcherPinSSRTemperature 13 //SST Hatcher pin

#define BlinkerPin 41 //Blinker pin
#define HatcherPinExtDS 43
#define HatcherPinIntDS 45
#define SetterPinDS2 47
#define SetterPinDS1 49
#define SetterPinDHT 51

// ************************************************
// General settings & definitions
// ************************************************
#define DHTType DHT22   // DHT 22  (AM2302)
#define RelayON 0 // Constants for Arduino relay board
#define RelayOFF 1
bool Debug = false;
bool Simulator = true;
int ledState = LOW;
int BlinkerSpeed; //Blinker speed

// ************************************************
// Sensors and devices
// ************************************************

//Initiate DHT sensors
DHT SetterDHT(SetterPinDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino
DHT HatcherIntDHT(HatcherPinIntDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino

//Initiate DS sensors
// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWireSetterDS1(SetterPinDS1);
OneWire oneWireSetterDS2(SetterPinDS2);
OneWire oneWireHatcherExt(HatcherPinExtDS);
OneWire oneWireHatcherInt(HatcherPinIntDS);

// Pass our oneWire reference to Dallas Temperature.
DallasTemperature SetterDS1(&oneWireSetterDS1);
DallasTemperature SetterDS2(&oneWireSetterDS2);
DallasTemperature HatcherDSExt(&oneWireHatcherExt);
DallasTemperature HatcherDSInt(&oneWireHatcherInt);

//Initiate SCD30 C02
Adafruit_SCD30  scd30;

//Initialize COZIR
SoftwareSerial Hatchersws(HatcherPinCozir1, HatcherPinCozir2);
COZIR Hatcherczr(&Hatchersws);

// RXTX
SerialTransfer myTransfer;

// ************************************************
// Targets
// ************************************************
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

// ************************************************
// Error counters
// ************************************************
//Keeping track of number of erroneous readings
long SetterDHTErrorCount = 0;
long HatcherExtDHTErrorCount = 0;
long HatcherIntDHTErrorCount = 0;

// ************************************************
// Smoothers
// ************************************************
//DHT Smoothing
const int numReadings = 60;
double SetterDHTReadings[numReadings];      // the readings from the analog input
int SetterDHTTempReadIndex = 0;              // the index of the current reading
double SetterDHTTempTotal = 0.0;                  // the running total
double SetterDHTTempAverage = 0.0;                // the average

double HatcherExtDSReadings[numReadings];      // the readings from the analog input
int HatcherExtDSTempReadIndex = 0;              // the index of the current reading
double HatcherExtDSTempTotal = 0.0;                  // the running total
double HatcherExtDSTempAverage = 0;                // the average

double HatcherIntDHTReadings[numReadings];      // the readings from the analog input
int HatcherIntDHTTempReadIndex = 0;              // the index of the current reading
double HatcherIntDHTTempTotal = 0.0;                  // the running total
double HatcherIntDHTTempAverage = 0.0;                // the average

// ************************************************
// Timers
// ************************************************
unsigned long SetterSensorTimer = 2500;
unsigned long SetterTemperatureTargetTimer = 4500;
unsigned long SetterWindowTimer = 5000;
unsigned long SetterEggTurnTimer = 0;
unsigned long HatcherSensorTimer = 2500;
unsigned long HatcherTemperatureTargetTimer = 4500;
unsigned long HatcherWindowTimer = 5000;
unsigned long BlinkerTimer = 0;
unsigned long RxTxTimer = 30000;

// **************************************************************
// * RX TX
// **************************************************************

struct STRUCTRX {
  byte SetterMode = 0;
  byte HatcherMode = 0;
  double SetterKp = 0.0;
  double SetterKi = 0.0;
  double SetterKd = 0.0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double SetterTempWindow = 250.0;
  double HatcherTempWindow = 0.0;
} settingsStructRX;

struct STRUCT {
  byte SetterMode = 1;
  byte HatcherMode = 0;
  double SetterKp = 0.0;
  double SetterKi = 0.0;
  double SetterKd = 0.0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double SetterTempWindow = 250.0;
  double HatcherTempWindow = 0.0;
  double SetterPIDWindow = 0.0;
  double HatcherPIDWindow = 0.0;
  double SetterWindow = 0.0;
  double HatcherWindow = 0.0;
  double SetterDHTTempAverage = 0.0;
  double SetterDHTHumidity = 0.0;
  double SetterSCD30Temperature = 0.0;
  double SetterSCD30Humidity = 0.0;
  double SetterSCD30CO2 = 0.0;
  double SetterDS1Temperature = 0.0;
  double SetterDS2Temperature = 0.0;
  double HatcherIntDHTTempAverage = 0.0;
  double HatcherIntDHTHumidity = 0.0;
  double HatcherIntDSTemperature = 0.0;
  double HatcherCozirTemperature = 0.0;
  double HatcherCozirHumidity = 0.0;
  double HatcherCozirCO2 = 0.0;
  
} settingsStruct;

// **************************************************************
// * Temperorary variables
// **************************************************************
//Setter variables
double SetterDHTTemperature; //Stores internal temperature value

//Hatcher variables
double HatcherIntDHTTemperature; //Stores internal temperature value
double HatcherExtDSTemperature; //Stores external temperature value

// ************************************************
// PID Variables and constants
// ************************************************

//Specify the links and initial tuning parameters
PID mySetterPID(
  &settingsStruct.SetterDHTTempAverage, 
  &settingsStruct.SetterPIDWindow, 
  &SetterTargetTemperature, 
  settingsStruct.SetterKp, 
  settingsStruct.SetterKi, 
  settingsStruct.SetterKd, 
  DIRECT);
PID myHatcherPID(
  &settingsStruct.HatcherIntDHTTempAverage, 
  &settingsStruct.HatcherPIDWindow, 
  &HatcherTargetIntTemperature, 
  settingsStruct.HatcherKp, 
  settingsStruct.HatcherKi, 
  settingsStruct.HatcherKd, 
  DIRECT);

void setup()
{
  if (Debug) {
    Serial.begin(115200);
  } else {
    Serial.begin(115200);
    myTransfer.begin(Serial);
  }
  
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

  // **************************************************************
  // * START SENSORS
  // ***************************************************************/
  // Try to initialize DHT sensors on
  SetterDHT.begin();
  HatcherIntDHT.begin();

  // Try to initialize DS sensors
  SetterDS1.begin();
  SetterDS2.begin();
  HatcherDSExt.begin();
  HatcherDSInt.begin();

  // Try to initialize SCD30 !
  if (!scd30.begin()) {
    if (Debug) Serial.println("Failed to find SCD30");
  } else {
    if (Debug) Serial.println("SCD30 found");
    }

  // **************************************************************
  // * PID
  // ***************************************************************/
  mySetterPID.SetMode(AUTOMATIC);
  mySetterPID.SetOutputLimits(100, 9000);
  mySetterPID.SetSampleTime(60000);
  myHatcherPID.SetMode(AUTOMATIC);
  myHatcherPID.SetOutputLimits(100, 9000);
  myHatcherPID.SetSampleTime(60000);

  // **************************************************************
  // * SMOOTHERS
  // ***************************************************************/
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    SetterDHTReadings[thisReading] = 0.0;
  }
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherExtDSReadings[thisReading] = 0.0;
  }
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherIntDHTReadings[thisReading] = 0.0;
  }

  // **************************************************************
  // * SETUP FINISHED
  // ***************************************************************/
  digitalWrite(BlinkerPin, HIGH);
  delay(5000);
  digitalWrite(BlinkerPin, LOW);
}


void loop()
{
  ToggleBlink();
  if (Debug == true) {
    SerialSend(10000);
  } else {
    SerialRxTx(10000);
  }
  Setter();
  Hatcher();
}

void SerialRxTx(unsigned long interval) {
  if (millis() - RxTxTimer >= interval && myTransfer.available()){
    RxTxTimer = millis();  
    {
      uint16_t recSize = 0;// use this variable to keep track of how many bytes we've processed from the receive buffer
      recSize = myTransfer.rxObj(settingsStructRX, recSize);
      
      UpdateRXtoTX();
      
      uint16_t sendSize = 0;// use this variable to keep track of how many bytes we're stuffing in the transmit buffer
      sendSize = myTransfer.txObj(settingsStruct, sendSize);// Stuff buffer with struct
      myTransfer.sendData(sendSize);// Send buffer
    }
  }
}

void UpdateRXtoTX() {
  settingsStruct.SetterMode = settingsStructRX.SetterMode;
  settingsStruct.HatcherMode = settingsStructRX.HatcherMode;
  settingsStruct.SetterKp = settingsStructRX.SetterKp;
  settingsStruct.SetterKi = settingsStructRX.SetterKi;
  settingsStruct.SetterKd = settingsStructRX.SetterKd;
  settingsStruct.HatcherKp = settingsStructRX.HatcherKp;
  settingsStruct.HatcherKi = settingsStructRX.HatcherKi;
  settingsStruct.HatcherKd = settingsStructRX.HatcherKd;
  settingsStruct.SetterTempWindow = settingsStructRX.SetterTempWindow;
  settingsStruct.HatcherTempWindow = settingsStructRX.HatcherTempWindow;
  }

void SerialSend(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - RxTxTimer >= interval){
    RxTxTimer = millis();
    UpdateRXtoTX();
    Serial.print("SetterMode: ");Serial.println(settingsStruct.SetterMode);
    Serial.print("HatcherMode: ");Serial.println(settingsStruct.HatcherMode);
    Serial.print("SetterKp: ");Serial.println(settingsStruct.SetterKp);
    Serial.print("SetterKi: ");Serial.println(settingsStruct.SetterKi);
    Serial.print("SetterKd: ");Serial.println(settingsStruct.SetterKd);
    Serial.print("HatcherKp: ");Serial.println(settingsStruct.HatcherKp);
    Serial.print("HatcherKi: ");Serial.println(settingsStruct.HatcherKi);
    Serial.print("HatcherKd: ");Serial.println(settingsStruct.HatcherKd);
    Serial.print("SetterTempWindow: ");Serial.println(settingsStruct.SetterTempWindow);
    Serial.print("HatcherTempWindow: ");Serial.println(settingsStruct.HatcherTempWindow);
    Serial.print("SetterWindow: ");Serial.println(settingsStruct.SetterWindow);
    Serial.print("HatcherWindow: ");Serial.println(settingsStruct.HatcherWindow);
    Serial.print("SetterDHTTempAverage: ");Serial.println(settingsStruct.SetterDHTTempAverage);
    Serial.print("SetterDHTErrors: ");Serial.println(SetterDHTErrorCount);
    Serial.print("SetterDHTHumidity: ");Serial.println(settingsStruct.SetterDHTHumidity);
    Serial.print("SetterSCD30Temperature: ");Serial.println(settingsStruct.SetterSCD30Temperature);
    Serial.print("SetterSCD30Humidity: ");Serial.println(settingsStruct.SetterSCD30Humidity);
    Serial.print("SetterSCD30CO2: ");Serial.println(settingsStruct.SetterSCD30CO2);
    Serial.print("SetterDS1Temperature: ");Serial.println(settingsStruct.SetterDS1Temperature);
    Serial.print("SetterDS2Temperature: ");Serial.println(settingsStruct.SetterDS2Temperature);
    Serial.print("HatcherIntDHTTempAverage: ");Serial.println(settingsStruct.HatcherIntDHTTempAverage);
    Serial.print("HatcherDHTErrors: ");Serial.println(HatcherIntDHTErrorCount);
    Serial.print("HatcherIntDHTHumidity: ");Serial.println(settingsStruct.HatcherIntDHTHumidity);
    Serial.print("HatcherIntDSTemperature: ");Serial.println(settingsStruct.HatcherIntDSTemperature);
    Serial.print("HatcherCozirTemperature: ");Serial.println(settingsStruct.HatcherCozirTemperature);
    Serial.print("HatcherCozirHumidity: ");Serial.println(settingsStruct.HatcherCozirHumidity);
    Serial.print("HatcherCozirCO2: ");Serial.println(settingsStruct.HatcherCozirCO2);
    }
  }

void Setter() {
  SetterReadSensors(10000); // every 10 seconds
  SetterPID();
  switch (settingsStruct.SetterMode) {
    case 0: {
      SetterOff();
      BlinkerSpeed = 100;
      }
      break;

    case 1 : {
      SetterManualMode();
      BlinkerSpeed = 1000;
      }
      break;
    case 2 : {
      SetterAutomaticMode(60000, false);
      BlinkerSpeed = 2500;
      }
      break;

    case 3: { // all good - show green
      SetterAutomaticMode(60000, false);
      BlinkerSpeed = 5000;
      }
      break;
  }
  SetterPWM(10000);
  SetterEggTurn(3600000); //every hour
}

void SetterManualMode() {
  settingsStruct.SetterWindow = settingsStruct.SetterTempWindow;
}

void SetterAutomaticMode(unsigned long interval, bool PID) {
  //Compute output with or without PID
  if ((millis() - SetterTemperatureTargetTimer >= interval) && (PID == true)) { 
    //time to shift the Relay Window
    if (Debug) Serial.println("PID ADJUST SETTER WINDOW");
    SetterTemperatureTargetTimer = millis();
    SetterPIDAdjustTemperatureWindow();
  } 
  else if ((millis() - SetterTemperatureTargetTimer >= interval) && (PID == false)) {
    //time to shift the Relay Window
    if (Debug) Serial.println("STEP ADJUST SETTER WINDOW");
    SetterTemperatureTargetTimer = millis();
    SetterStepAdjustTemperatureWindow();
  }
}

void SetterPIDAdjustTemperatureWindow() {
  settingsStruct.SetterWindow = settingsStruct.SetterPIDWindow;
}

void SetterStepAdjustTemperatureWindow() {
  if ((settingsStruct.SetterDHTTempAverage > (SetterTargetTemperature + 0.15)))
  {
    settingsStruct.SetterWindow -= 20.0;
  }
  else if ((settingsStruct.SetterDHTTempAverage > (SetterTargetTemperature + 0.1)))
  {
    settingsStruct.SetterWindow -= 10.0;
  }
  else if (settingsStruct.SetterDHTTempAverage < (SetterTargetTemperature - 0.2))
  {
    settingsStruct.SetterWindow += 10.0;
  }
  else if (settingsStruct.SetterDHTTempAverage < (SetterTargetTemperature - 0.1))
  {
    settingsStruct.SetterWindow += 5.0;
  }
}

void SetterPID() {
  mySetterPID.SetTunings(settingsStruct.SetterKp, settingsStruct.SetterKi, settingsStruct.SetterKd);
  mySetterPID.Compute();
}

void SetterOff() {
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(SetterPinSSRTemperature, LOW);
}

void SetterReadSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - SetterSensorTimer >= interval)
  {
    if (Debug) Serial.println("Checking setter sensors");
    SetterSensorTimer = millis(); //reset timer
      if (Simulator) {
          if (Debug) Serial.println("Using random values setter sensors");
          SetterDHTTemperature = random(370, 380) / 10.0;          
          settingsStruct.SetterDHTHumidity = random(400, 500) / 10.0;
          settingsStruct.SetterSCD30Temperature = random(370, 380) / 10.0;
          settingsStruct.SetterSCD30Humidity = random(400, 500) / 10.0;
          settingsStruct.SetterSCD30CO2 = random(500, 5000);
          settingsStruct.SetterDS1Temperature = random(370, 380) / 10.0;
          settingsStruct.SetterDS2Temperature = random(370, 380) / 10.0;
          settingsStruct.SetterWindow = settingsStructRX.SetterTempWindow;
      } else {
          if (Debug) Serial.println("Using real values setter sensors");
          float SetterDHTHumidityReading = SetterDHT.readHumidity();
          float SetterDHTTemperatureReading = SetterDHT.readTemperature();          
          if (isnan(SetterDHTTemperatureReading))
            {
              if (Debug) Serial.println("Setter DHT error");
              SetterDHTErrorCount += 1;
              return;
            }
          else {
            SetterDHTTemperature = SetterDHTTemperatureReading;
            settingsStruct.SetterDHTHumidity = SetterDHTHumidityReading;            
            }
          SetterDS1.requestTemperatures();
          settingsStruct.SetterDS1Temperature = SetterDS1.getTempCByIndex(0);
          SetterDS2.requestTemperatures();
          settingsStruct.SetterDS2Temperature = SetterDS2.getTempCByIndex(0); 
          scd30.read();
          settingsStruct.SetterSCD30Temperature = scd30.temperature;
          settingsStruct.SetterSCD30Humidity = scd30.relative_humidity;
          settingsStruct.SetterSCD30CO2 = scd30.CO2;
      } 

      SetterDHTTempTotal = SetterDHTTempTotal - SetterDHTReadings[SetterDHTTempReadIndex];// subtract the last reading:
      SetterDHTReadings[SetterDHTTempReadIndex] = SetterDHTTemperature;// read from the sensor:    
      SetterDHTTempTotal = SetterDHTTempTotal + SetterDHTReadings[SetterDHTTempReadIndex];// add the reading to the total:
      SetterDHTTempReadIndex = SetterDHTTempReadIndex + 1;// advance to the next position in the array:
      if (SetterDHTTempReadIndex >= numReadings) {
        // ...wrap around to the beginning:
        SetterDHTTempReadIndex = 0;
      }
      settingsStruct.SetterDHTTempAverage = SetterDHTTempTotal / numReadings;// calculate the average:
  }
}

void SetterEggTurn(unsigned long interval) {
  /************************************************
    SETTER TURNING
  ************************************************/
  if (millis() - SetterEggTurnTimer >= interval)
  {
    if (Debug) Serial.println("Turning Eggs");
    SetterEggTurnTimer = millis();
    digitalWrite(SetterPinRelayEggTurner, RelayON);
    delay(12000); //2.5 rpm at 50 Hz -> 12 sec for half turn
    digitalWrite(SetterPinRelayEggTurner, RelayOFF);
  }
}

void SetterPWM(unsigned long interval) {
  if (millis() - SetterWindowTimer >= interval)
  { //time to shift the Relay Window
    if (Debug) Serial.println("Checking setter window");
    SetterWindowTimer += interval;
  }
  if (settingsStruct.SetterWindow > millis() - SetterWindowTimer) digitalWrite(SetterPinSSRTemperature, HIGH);
  else digitalWrite(SetterPinSSRTemperature, LOW);
}

void Hatcher() {
  HatcherReadSensors(10000);
  HatcherExtTemperatureCheck();
  HatcherHumidityCheck();
  HatcherPID();
  switch (settingsStruct.HatcherMode) {
    case 0: {
      HatcherOff();
      }
      break;

    case 1 : {
      HatcherManualMode();
      }
      break;
    case 2 : {
      HatcherAutomaticMode(60000, false);
      }
      break;

    case 3: {
      HatcherAutomaticMode(60000, false);
      }
      break;
  }
  HatcherPWM(10000);
}

void HatcherOff() {
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(HatcherPinSSRTemperature, LOW);
}

void HatcherReadSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - HatcherSensorTimer >= interval)
  {
    HatcherSensorTimer = millis(); //reset timer
    if (Debug) Serial.println("Checking hatcher sensors");
    if (isnan(HatcherIntDHT.readTemperature()) ||  abs(HatcherIntDHT.readTemperature() - HatcherIntDHTReadings[HatcherIntDHTTempReadIndex]) > 10.0)
    {
      HatcherIntDHTErrorCount += 1;
      return;
    }
    else
    {
      if (Simulator) {
        if (Debug) Serial.println("Using random values hatcher sensors");
        HatcherIntDHTTemperature = random(370, 380) / 10.0;
        settingsStruct.HatcherIntDHTHumidity = random(550, 650) / 10.0;
        settingsStruct.HatcherIntDSTemperature = random(370, 380) / 10.0;
        settingsStruct.HatcherCozirTemperature = random(370, 380) / 10.0;
        settingsStruct.HatcherCozirHumidity = random(550, 650) / 10.0;
        settingsStruct.HatcherCozirCO2 = random(500, 5000);
        settingsStruct.HatcherWindow = settingsStructRX.HatcherTempWindow;
      } else {
        if (Debug) Serial.println("Using real values hatcher sensors");
        settingsStruct.HatcherIntDHTHumidity = HatcherIntDHT.readHumidity();
        HatcherIntDHTTemperature = HatcherIntDHT.readTemperature();
        HatcherDSInt.requestTemperatures();
        settingsStruct.HatcherIntDSTemperature = HatcherDSInt.getTempCByIndex(0);
        settingsStruct.HatcherCozirTemperature = Hatcherczr.Celsius();
        settingsStruct.HatcherCozirHumidity = Hatcherczr.Humidity();
        settingsStruct.HatcherCozirCO2 = Hatcherczr.CO2();
      }
      // Smoothing algorythm
      HatcherIntDHTTempTotal = HatcherIntDHTTempTotal - HatcherIntDHTReadings[HatcherIntDHTTempReadIndex];// subtract the last reading:
      HatcherIntDHTReadings[HatcherIntDHTTempReadIndex] = HatcherIntDHTTemperature;// read from the sensor:
      HatcherIntDHTTempTotal = HatcherIntDHTTempTotal + HatcherIntDHTReadings[HatcherIntDHTTempReadIndex];// add the reading to the total:
      HatcherIntDHTTempReadIndex = HatcherIntDHTTempReadIndex + 1;// advance to the next position in the array:

      // if we're at the end of the array...
      if (HatcherIntDHTTempReadIndex >= numReadings) {
        HatcherIntDHTTempReadIndex = 0;// ...wrap around to the beginning:
      }
      settingsStruct.HatcherIntDHTTempAverage = HatcherIntDHTTempTotal / numReadings;// calculate the average:
    }

    if (isnan(HatcherDSExt.getTempCByIndex(0)) || HatcherDSExt.getTempCByIndex(0) < 10.0 || abs(HatcherDSExt.getTempCByIndex(0) - HatcherExtDSReadings[HatcherExtDSTempReadIndex]) > 10.0)
    {
      HatcherExtDHTErrorCount += 1;
      //return;
    }
    else
    {
      HatcherDSExt.requestTemperatures();
      HatcherExtDSTemperature = HatcherDSExt.getTempCByIndex(0);
      // Smoothing algorythm
      HatcherExtDSTempTotal = HatcherExtDSTempTotal - HatcherExtDSReadings[HatcherExtDSTempReadIndex];// subtract the last reading:
      HatcherExtDSReadings[HatcherExtDSTempReadIndex] = HatcherExtDSTemperature;// read from the sensor:
      HatcherExtDSTempTotal = HatcherExtDSTempTotal + HatcherExtDSReadings[HatcherExtDSTempReadIndex];// add the reading to the total:
      HatcherExtDSTempReadIndex = HatcherExtDSTempReadIndex + 1;// advance to the next position in the array:

      // if we're at the end of the array...
      if (HatcherExtDSTempReadIndex >= numReadings) {
        // ...wrap around to the beginning:
        HatcherExtDSTempReadIndex = 0;
      }
      // calculate the average:
      HatcherExtDSTempAverage = HatcherExtDSTempTotal / numReadings;
      // send it to the computer as ASCII digits
    }
  }
}

void HatcherManualMode() {
  settingsStruct.HatcherWindow = settingsStruct.HatcherTempWindow;
}

void HatcherExtTemperatureCheck() {
  //HATCHER TEMPERATURE CHECK
  if (HatcherExtDSTemperature > HatcherTargetExtTemperature + 0.2) digitalWrite(HatcherPinSSRTemperature, LOW);
  else if (HatcherExtDSTemperature < HatcherTargetExtTemperature - 0.2) digitalWrite(HatcherPinSSRTemperature, HIGH);
}

void HatcherHumidityCheck() {
  //SET HATCHER HUMIDITY
  if (settingsStruct.HatcherIntDHTHumidity > HatcherTargetIntHumidity + 5.0) digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  else if (settingsStruct.HatcherIntDHTHumidity < HatcherTargetIntHumidity - 5.0) digitalWrite(HatcherPinRelayHumidity, RelayON);
}

void HatcherAutomaticMode(unsigned long interval, bool PID) {
  //Compute output with or without PID
  if ((millis() - HatcherTemperatureTargetTimer >= interval) && (PID == true))
  { //time to shift the Relay Window
    if (Debug) Serial.println("PID ADJUST HATCHER WINDOW");
    HatcherTemperatureTargetTimer = millis();
    HatcherPIDAdjustTemperatureWindow();
  }
  else if ((millis() - HatcherTemperatureTargetTimer >= interval) && (PID == false)) {
    //time to shift the Relay Window
    if (Debug) Serial.println("STEP ADJUST SETTER WINDOW");
    HatcherTemperatureTargetTimer = millis();
    HatcherStepAdjustTemperatureTarget();
    }
  }
void HatcherPID() {
  myHatcherPID.SetTunings(settingsStruct.HatcherKp, settingsStruct.HatcherKi, settingsStruct.HatcherKd);
  myHatcherPID.Compute();
}

void HatcherPIDAdjustTemperatureWindow() {
  settingsStruct.HatcherWindow = settingsStruct.HatcherPIDWindow;
}

void HatcherStepAdjustTemperatureTarget() {
    //time to shift the temperature set 0.2 down or 0.1 up
    HatcherTemperatureTargetTimer =  millis();
    if (HatcherIntDHTTemperature > HatcherTargetIntTemperature + 0.3) {
      HatcherTargetExtTemperature -= 0.5;
    }
    else if (HatcherIntDHTTemperature < HatcherTargetIntTemperature - 0.3) {
      HatcherTargetExtTemperature += 0.1;
    }
}

void HatcherPWM(unsigned long interval) {
  if (millis() - HatcherWindowTimer >= interval)
  { //time to shift the Relay Window
    HatcherWindowTimer += interval;
  }
  if (settingsStruct.HatcherWindow > millis() - HatcherWindowTimer) digitalWrite(HatcherPinSSRTemperature, HIGH);
  else digitalWrite(HatcherPinSSRTemperature, LOW);
}

void ToggleBlink() {
  if (Simulator == true) {
    BlinkerSpeed = 50;
  }
  //Watch out, number 13 pin is LED_BUILTIN
  if (millis() - BlinkerTimer >= BlinkerSpeed) {
    // save the last time you blinked the LED
    BlinkerTimer = millis();
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
