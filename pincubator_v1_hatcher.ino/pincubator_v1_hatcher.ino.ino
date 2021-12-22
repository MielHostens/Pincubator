#include "DHT.h"
#include "PID_v1.h"
#include "OneWire.h"
#include "DallasTemperature.h"
#include "Adafruit_SCD30.h"
#include "SerialTransfer.h"

// ************************************************
// Pin definitions & sensors
// ************************************************

#define HatcherPinRelayHumidity 4 // Pin for relay for humidity in hatcher
#define HatcherPinSSRTemperature 3 //SST Hatcher pin
#define SetterPinDS 5
#define HatcherPinIntDS 6
#define HatcherPinExtDS 7
#define BlinkerPin 2 //Blinker pin

// ************************************************
// General settings & definitions
// ************************************************
#define DHTType DHT22   // DHT 22  (AM2302)
#define RelayON 0 // Constants for Arduino relay board
#define RelayOFF 1
bool Debug = false;
bool Simulator = false;
int ledState = LOW;
int BlinkerSpeed; //Blinker speed

// ************************************************
// Sensors and devices
// ************************************************

//Initiate DS sensors
// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWireHatcherExt(HatcherPinExtDS);
OneWire oneWireHatcherInt(HatcherPinIntDS);
OneWire oneWireSetterDS(SetterPinDS);

// Pass our oneWire reference to Dallas Temperature.

DallasTemperature HatcherIntDS(&oneWireHatcherInt);
DallasTemperature HatcherExtDS(&oneWireHatcherExt);
DallasTemperature SetterDS(&oneWireSetterDS);

//Initiate SCD30 C02
Adafruit_SCD30  scd30;

// RXTX
SerialTransfer myTransfer;

// ************************************************
// Targets
// ************************************************
//Hatcher goals
double HatcherTargetExtTemperature = 40.1;  //Setting external temperature value
double HatcherTargetIntTemperature = 37.6;
double HatcherTargetIntHumidity = 65.0; //Stores internal temperature value

// ************************************************
// Error counters
// ************************************************
//Keeping track of number of erroneous readings
unsigned long HatcherExtDSErrorCount = 0;
unsigned long HatcherIntDSErrorCount = 0;

// ************************************************
// Smoothers
// ************************************************
//DHT Smoothing
const int numReadings = 60;

double HatcherExtDSTemperatureReadings[numReadings];      // the readings from the analog input
int HatcherExtDSTempReadIndex = 0;              // the index of the current reading
double HatcherExtDSTempTotal = 0.0;                  // the running total
double HatcherExtDSTempAverage = 0;                // the average

double HatcherIntDSTemperatureReadings[numReadings];      // the readings from the analog input
int HatcherIntDSTempReadIndex = 0;              // the index of the current reading
double HatcherIntDSTempTotal = 0.0;                  // the running total
double HatcherIntDSTempAverage = 0.0;                // the average

// ************************************************
// Timers
// ************************************************
unsigned long HatcherSensorTimer = 2500;
unsigned long HatcherSensorEssentialTimer = 2500;
unsigned long HatcherTemperatureTargetTimer = 0;
unsigned long HatcherWindowTimer = 5000;
unsigned long BlinkerTimer = 0;
unsigned long RxTxTimer = 28000;

// **************************************************************
// * RX TX
// **************************************************************

struct STRUCTRX {
  byte HatcherMode = 0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double HatcherMaxWindow = 0.0;
  double HatcherMinWindow = 0.0;
} settingsStructRX;

struct STRUCT {
  byte HatcherMode = 0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double HatcherMaxWindow = 0.0;
  double HatcherMinWindow = 0.0;
  double HatcherPIDWindow = 0.0;
  double HatcherWindow = 0.0;
  double HatcherIntDSTempAverage = 0.0;
  double HatcherIntDSTemperature = 0.0;
  double HatcherIntDSErrorCount = 0.0;  
  double HatcherExtDSTempAverage = 0.0;
  double HatcherExtDSTemperature = 0.0;
  double HatcherExtDSErrorCount = 0.0; 
  double HatcherSCD30Temperature = 0.0;
  double HatcherSCD30Humidity = 0.0;
  double HatcherSCD30CO2 = 0.0;
  double SetterDSTemperature = 0.0;
} settingsStruct;

// ************************************************
// PID Variables and constants
// ************************************************

PID myHatcherPID(
  &settingsStruct.HatcherIntDSTempAverage, 
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

  pinMode(HatcherPinRelayHumidity, OUTPUT);
  pinMode(HatcherPinSSRTemperature, OUTPUT);
  pinMode(BlinkerPin, OUTPUT);
  
  // Initialize Pins so relays are inactive at reset
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(HatcherPinSSRTemperature, LOW);

  // **************************************************************
  // * START SENSORS
  // ***************************************************************/
  // Try to initialize DS sensors
  HatcherIntDS.begin();  
  HatcherExtDS.begin();
  SetterDS.begin();

  // Try to initialize SCD30 !
  if (!scd30.begin()) {
    if (Debug) Serial.println("Failed to find SCD30");
  } else {
    if (Debug) Serial.println("SCD30 found");
    }

  // **************************************************************
  // * PID
  // ***************************************************************/
  myHatcherPID.SetMode(AUTOMATIC);
  myHatcherPID.SetOutputLimits(100, 9000);
  myHatcherPID.SetSampleTime(60000);

  // **************************************************************
  // * SMOOTHERS
  // ***************************************************************/
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherExtDSTemperatureReadings[thisReading] = 0.0;
  }
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    HatcherIntDSTemperatureReadings[thisReading] = 0.0;
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
  settingsStruct.HatcherMode = settingsStructRX.HatcherMode;
  settingsStruct.HatcherKp = settingsStructRX.HatcherKp;
  settingsStruct.HatcherKi = settingsStructRX.HatcherKi;
  settingsStruct.HatcherKd = settingsStructRX.HatcherKd;
  settingsStruct.HatcherMaxWindow = settingsStructRX.HatcherMaxWindow;
  settingsStruct.HatcherMinWindow = settingsStructRX.HatcherMinWindow;
  }

void SerialSend(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - RxTxTimer >= interval){
    RxTxTimer = millis();
    UpdateRXtoTX();
    Serial.print("HatcherMode: ");Serial.println(settingsStruct.HatcherMode);
    Serial.print("HatcherKp: ");Serial.println(settingsStruct.HatcherKp);
    Serial.print("HatcherKi: ");Serial.println(settingsStruct.HatcherKi);
    Serial.print("HatcherKd: ");Serial.println(settingsStruct.HatcherKd);
    Serial.print("HatcherMaxWindow: ");Serial.println(settingsStruct.HatcherMaxWindow);
    Serial.print("HatcherMinWindow: ");Serial.println(settingsStruct.HatcherMinWindow);
    Serial.print("HatcherWindow: ");Serial.println(settingsStruct.HatcherWindow);
    Serial.print("HatcherIntDSTempAverage: ");Serial.println(settingsStruct.HatcherIntDSTempAverage);
    Serial.print("HatcherIntDSTemperature: ");Serial.println(settingsStruct.HatcherIntDSTemperature);
    Serial.print("HatcherIntDSErrors: ");Serial.println(HatcherIntDSErrorCount);
    Serial.print("HatcherExtDSTemperature: ");Serial.println(settingsStruct.HatcherExtDSTemperature);
    Serial.print("HatcherExtDSErrors: ");Serial.println(HatcherExtDSErrorCount);
    Serial.print("HatcherSCD30Temperature: ");Serial.println(settingsStruct.HatcherSCD30Temperature);
    Serial.print("HatcherSCD30Humidity: ");Serial.println(settingsStruct.HatcherSCD30Humidity);
    Serial.print("HatcherSCD30CO2: ");Serial.println(settingsStruct.HatcherSCD30CO2);
    Serial.print("SetterDSTemperature: ");Serial.println(settingsStruct.SetterDSTemperature);
    }
  }

void Hatcher() {
  HatcherReadEssentialSensors(10000); // every 10 seconds
  HatcherReadSensors(10000); // every 10 seconds
  HatcherPID();
  switch (settingsStruct.HatcherMode) {
    case 0: {
      HatcherOff();
      BlinkerSpeed = 5000;
      }
      break;

    case 1 : {
      HatcherManualMode();
      BlinkerSpeed = 2500;
      }
      break;
    case 2 : {
      HatcherAutomaticMode(3600000, false);
      BlinkerSpeed = 1000;
      }
      break;

    case 3: { // all good - show green
      HatcherAutomaticMode(60000, true);
      BlinkerSpeed = 100;
      }
      break;
  }
  HatcherExtTemperatureCheck();
  HatcherHumidityCheck();
  HatcherPWM(10000);
}

void HatcherOff() {
  //SHUT DOWN HATCHER ENTIRELY
  settingsStruct.HatcherWindow = 0.0;
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(HatcherPinSSRTemperature, LOW);
}

void HatcherReadEssentialSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - HatcherSensorEssentialTimer >= interval)
  {
    if (Debug) Serial.println("Checking setter sensors");
    HatcherSensorEssentialTimer = millis(); //reset timer
      if (Simulator) {
          if (Debug) Serial.println("Using random values setter essential sensors");
          settingsStruct.HatcherIntDSTemperature = random(370, 380) / 10.0;
          settingsStruct.HatcherExtDSTemperature = random(370, 380) / 10.0;
      } else {
          if (Debug) Serial.println("Using real values setter essential sensors");
          //Internal readings
          HatcherIntDS.requestTemperatures();
          double HatcherDSIntTemperatureReading = HatcherIntDS.getTempCByIndex(0);       
          if (isnan(HatcherDSIntTemperatureReading))
            {
              if (Debug) Serial.println("Hatcher Int DS error");
              settingsStruct.HatcherIntDSErrorCount += 1;
              HatcherDSIntTemperatureReading = settingsStruct.HatcherSCD30Temperature; // BACKUP
            }
          else {
            settingsStruct.HatcherIntDSTemperature = HatcherDSIntTemperatureReading;           
            }
          HatcherIntDSTempTotal = HatcherIntDSTempTotal - HatcherIntDSTemperatureReadings[HatcherIntDSTempReadIndex];// subtract the last reading:
          HatcherIntDSTemperatureReadings[HatcherIntDSTempReadIndex] = HatcherDSIntTemperatureReading;// read from the sensor:    
          HatcherIntDSTempTotal = HatcherIntDSTempTotal + HatcherIntDSTemperatureReadings[HatcherIntDSTempReadIndex];// add the reading to the total:
          HatcherIntDSTempReadIndex = HatcherIntDSTempReadIndex + 1;// advance to the next position in the array:
          if (HatcherIntDSTempReadIndex >= numReadings) {
            // ...wrap around to the beginning:
            HatcherIntDSTempReadIndex = 0;
          }
          settingsStruct.HatcherIntDSTempAverage = HatcherIntDSTempTotal / numReadings;// calculate the average:
          
          //External readings
          HatcherExtDS.requestTemperatures();
          double HatcherDSExtTemperatureReading = HatcherExtDS.getTempCByIndex(0);       
          if (isnan(HatcherDSExtTemperatureReading))
            {
              if (Debug) Serial.println("Hatcher Ext DS error");
              settingsStruct.HatcherExtDSErrorCount += 1;
            }
          else {
            settingsStruct.HatcherExtDSTemperature = HatcherDSExtTemperatureReading;           
            }
          HatcherExtDSTempTotal = HatcherExtDSTempTotal - HatcherExtDSTemperatureReadings[HatcherExtDSTempReadIndex];// subtract the last reading:
          HatcherExtDSTemperatureReadings[HatcherExtDSTempReadIndex] = HatcherDSExtTemperatureReading;// read from the sensor:    
          HatcherExtDSTempTotal = HatcherExtDSTempTotal + HatcherExtDSTemperatureReadings[HatcherExtDSTempReadIndex];// add the reading to the total:
          HatcherExtDSTempReadIndex = HatcherExtDSTempReadIndex + 1;// advance to the next position in the array:
          if (HatcherExtDSTempReadIndex >= numReadings) {
            // ...wrap around to the beginning:
            HatcherExtDSTempReadIndex = 0;
          }
          settingsStruct.HatcherExtDSTempAverage = HatcherExtDSTempTotal / numReadings;// calculate the average:
      }
  }
}

void HatcherReadSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - HatcherSensorTimer >= interval)
  {
    if (Debug) Serial.println("Checking setter sensors");
    HatcherSensorTimer = millis(); //reset timer
      if (Simulator) {
          if (Debug) Serial.println("Using random values setter sensors");
          settingsStruct.HatcherSCD30Temperature = random(370, 380) / 10.0;
          settingsStruct.HatcherSCD30Humidity = random(400, 500) / 10.0;
          settingsStruct.HatcherSCD30CO2 = random(500, 5000);
          settingsStruct.HatcherWindow = settingsStructRX.HatcherMaxWindow;
          settingsStruct.SetterDSTemperature = random(370, 380) / 10.0;       
      } else {
          if (Debug) Serial.println("Using real values setter sensors");
          scd30.read();
          settingsStruct.HatcherSCD30Temperature = scd30.temperature;
          settingsStruct.HatcherSCD30Humidity = scd30.relative_humidity;
          settingsStruct.HatcherSCD30CO2 = scd30.CO2;
          SetterDS.requestTemperatures();
          settingsStruct.SetterDSTemperature = SetterDS.getTempCByIndex(0); 
      }
  }
}

void HatcherManualMode() {
  settingsStruct.HatcherWindow = settingsStruct.HatcherMaxWindow;
}

void HatcherExtTemperatureCheck() {
  //HATCHER TEMPERATURE CHECK
  if (settingsStruct.HatcherExtDSTemperature > HatcherTargetExtTemperature + 0.2) digitalWrite(HatcherPinSSRTemperature, LOW);
  else if (settingsStruct.HatcherExtDSTemperature < HatcherTargetExtTemperature - 0.2) digitalWrite(HatcherPinSSRTemperature, HIGH);
}

void HatcherHumidityCheck() {
  //SET HATCHER HUMIDITY
  if (settingsStruct.HatcherSCD30Humidity > HatcherTargetIntHumidity + 5.0) digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  else if (settingsStruct.HatcherSCD30Humidity < HatcherTargetIntHumidity - 5.0) digitalWrite(HatcherPinRelayHumidity, RelayON);
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
  myHatcherPID.SetOutputLimits(settingsStruct.HatcherMinWindow, settingsStruct.HatcherMaxWindow);
  myHatcherPID.SetTunings(settingsStruct.HatcherKp, settingsStruct.HatcherKi, settingsStruct.HatcherKd);
  myHatcherPID.Compute();
}

void HatcherPIDAdjustTemperatureWindow() {
  settingsStruct.HatcherWindow = settingsStruct.HatcherPIDWindow;
}

void HatcherStepAdjustTemperatureTarget() {
    //time to shift the temperature set 0.2 down or 0.1 up
    HatcherTemperatureTargetTimer =  millis();
    if (settingsStruct.HatcherIntDSTempAverage > HatcherTargetIntTemperature + 0.3) {
      HatcherTargetExtTemperature -= 0.5;
    }
    else if (settingsStruct.HatcherIntDSTempAverage < HatcherTargetIntTemperature - 0.3) {
      HatcherTargetExtTemperature += 0.1;
    }
}

void HatcherPWM(unsigned long interval) {
  settingsStruct.HatcherWindow = min(settingsStruct.HatcherWindow, settingsStruct.HatcherMaxWindow);
  settingsStruct.HatcherWindow = max(settingsStruct.HatcherWindow, settingsStruct.HatcherMinWindow);
  if (millis() - HatcherWindowTimer >= interval)
  { //time to shift the Relay Window
    HatcherWindowTimer += interval;
  }
  if (settingsStruct.HatcherWindow > millis() - HatcherWindowTimer) digitalWrite(HatcherPinSSRTemperature, HIGH);
  else digitalWrite(HatcherPinSSRTemperature, LOW);
}

void ToggleBlink() {
  if (Simulator == true) {
    //BlinkerSpeed = 50;
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
