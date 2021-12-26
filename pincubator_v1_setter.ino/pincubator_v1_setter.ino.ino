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
#define BlinkerPin 2 //Blinker pin
#define SetterPinSSREggTurner 11 // Pin for relay for egg turner in setter 
#define SetterPinSSRTemperature 4 //SSR Setter pin
#define SetterPinDHT 5
#define SetterPinDS1 6
#define SetterPinDS2 7
#define HatcherPinDS1 8

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

//Initiate DHT sensors
DHT SetterDHT(SetterPinDHT, DHTType); //// Initialize DHT sensor for normal 16mhz Arduino

//Initiate DS sensors
// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWireSetterDS1(SetterPinDS1);
OneWire oneWireSetterDS2(SetterPinDS2);
OneWire oneWireHatcherDS1(HatcherPinDS1);

// Pass our oneWire reference to Dallas Temperature.
DallasTemperature SetterDS1(&oneWireSetterDS1);
DallasTemperature SetterDS2(&oneWireSetterDS2);
DallasTemperature HatcherDS1(&oneWireHatcherDS1);

//Initiate SCD30 C02
Adafruit_SCD30  scd30;

// RXTX
SerialTransfer myTransfer;

// ************************************************
// Targets
// ************************************************
//Setter goals
double SetterTargetTemperature = 37.8;
double SetterTargetHumidity = 45.0;

//CO2 goals
int SetterTargetCO2 = 5000; //Max ppm

// ************************************************
// Smoothers
// ************************************************
//DHT Smoothing
const int numReadings = 60;
double SetterReadings[numReadings];      // the readings from the analog input
int SetterTempReadIndex = 0;              // the index of the current reading
double SetterTempTotal = 0.0;                  // the running total

// ************************************************
// Timers
// ************************************************
unsigned long SetterSensorEssentialTimer = 2500;
unsigned long SetterSensorTimer = 2500;
unsigned long SetterTemperatureTargetTimer = 0;
unsigned long SetterWindowTimer = 5000;
unsigned long SetterEggTurnTimer = 0;
unsigned long BlinkerTimer = 0;
unsigned long RxTxTimer = 28000;

// **************************************************************
// * RX TX
// **************************************************************

struct STRUCTRX {
  byte SetterMode = 3;
  double SetterKp = 500.0;
  double SetterKi = 0.1;
  double SetterKd = 0.0;
  double SetterMaxWindow = 2000.0;
  double SetterMinWindow = 500.0;
} settingsStructRX;

struct STRUCT {
  byte SetterMode = 3;
  double SetterKp = 2500.0;
  double SetterKi = 0.0;
  double SetterKd = 0.0;
  double SetterMaxWindow = 5000.0;
  double SetterMinWindow = 500.0;
  double SetterPIDWindow = 0.0;
  double SetterWindow = 0.0;
  double SetterDHTTemperature = 0.0;
  double SetterDHTHumidity = 0.0;
  double SetterTemperatureAverage = 0.0;
  double SetterSCD30Temperature = 0.0;
  double SetterSCD30Humidity = 0.0;
  double SetterSCD30CO2 = 0.0;
  double SetterDS1Temperature = 0.0;
  double SetterDS2Temperature = 0.0;
  double SetterErrorCount = 0.0;
  double HatcherDS1Temperature = 0.0;
} settingsStruct;

// ************************************************
// PID Variables and constants
// ************************************************

//Specify the links and initial tuning parameters
PID mySetterPID(
  &settingsStruct.SetterTemperatureAverage, 
  &settingsStruct.SetterPIDWindow, 
  &SetterTargetTemperature, 
  settingsStruct.SetterKp, 
  settingsStruct.SetterKi, 
  settingsStruct.SetterKd, 
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
  pinMode(SetterPinSSREggTurner, OUTPUT);
  pinMode(SetterPinSSRTemperature, OUTPUT);
  pinMode(BlinkerPin, OUTPUT);
  
  // Initialize Pins so relays are inactive at reset
  digitalWrite(SetterPinSSREggTurner, LOW);
  digitalWrite(SetterPinSSRTemperature, LOW);

  // **************************************************************
  // * START SENSORS
  // ***************************************************************/
  // Try to initialize DHT sensors on
  SetterDHT.begin();

  // Try to initialize DS sensors
  SetterDS1.begin();
  SetterDS2.begin();
  HatcherDS1.begin();

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

  // **************************************************************
  // * SMOOTHERS
  // ***************************************************************/
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    SetterReadings[thisReading] = 0.0;
  }

  // **************************************************************
  // * SETUP FINISHED
  // ***************************************************************/
  digitalWrite(SetterPinSSREggTurner, HIGH);
  delay(3000);
  digitalWrite(SetterPinSSREggTurner, LOW);
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
  settingsStruct.SetterKp = settingsStructRX.SetterKp;
  settingsStruct.SetterKi = settingsStructRX.SetterKi;
  settingsStruct.SetterKd = settingsStructRX.SetterKd;
  settingsStruct.SetterMaxWindow = settingsStructRX.SetterMaxWindow;
  settingsStruct.SetterMinWindow = settingsStructRX.SetterMinWindow;
  }

void SerialSend(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - RxTxTimer >= interval){
    RxTxTimer = millis();
    UpdateRXtoTX();
    Serial.print("SetterMode: ");Serial.println(settingsStruct.SetterMode);
    Serial.print("SetterKp: ");Serial.println(settingsStruct.SetterKp);
    Serial.print("SetterKi: ");Serial.println(settingsStruct.SetterKi);
    Serial.print("SetterKd: ");Serial.println(settingsStruct.SetterKd);
    Serial.print("SetterMaxWindow: ");Serial.println(settingsStruct.SetterMaxWindow);
    Serial.print("SetterMinWindow: ");Serial.println(settingsStruct.SetterMinWindow);
    Serial.print("SetterWindow: ");Serial.println(settingsStruct.SetterWindow);
    Serial.print("SetterTemperatureAverage: ");Serial.println(settingsStruct.SetterTemperatureAverage);
    Serial.print("SetterDHTTemperature: ");Serial.println(settingsStruct.SetterDHTTemperature);
    Serial.print("SetterDHTHumidity: ");Serial.println(settingsStruct.SetterDHTHumidity);
    Serial.print("SetterErrorCount: ");Serial.println(settingsStruct.SetterErrorCount);    
    Serial.print("SetterSCD30Temperature: ");Serial.println(settingsStruct.SetterSCD30Temperature);
    Serial.print("SetterSCD30Humidity: ");Serial.println(settingsStruct.SetterSCD30Humidity);
    Serial.print("SetterSCD30CO2: ");Serial.println(settingsStruct.SetterSCD30CO2);
    Serial.print("SetterDS1Temperature: ");Serial.println(settingsStruct.SetterDS1Temperature);
    Serial.print("SetterDS2Temperature: ");Serial.println(settingsStruct.SetterDS2Temperature);
    Serial.print("HatcherDS1Temperature: ");Serial.println(settingsStruct.HatcherDS1Temperature);
    }
  }

void Setter() {
  SetterReadEssentialSensors(10000); // every 10 seconds
  SetterReadSensors(10000); // every 10 seconds
  SetterPID();
  switch (settingsStruct.SetterMode) {
    case 0: {
      SetterOff();
      BlinkerSpeed = 5000;
      }
      break;

    case 1 : {
      SetterManualMode();
      BlinkerSpeed = 2500;
      }
      break;
    case 2 : {
      SetterAutomaticMode(3600000, false);
      BlinkerSpeed = 1000;
      }
      break;

    case 3: {
      SetterAutomaticMode(60000, true);
      BlinkerSpeed = 100;
      }
      break;
  }
  SetterPWM(10000);
  SetterEggTurn(3600000); //every hour
}

void SetterManualMode() {
  settingsStruct.SetterWindow = settingsStruct.SetterMaxWindow;
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
  if ((settingsStruct.SetterTemperatureAverage > (SetterTargetTemperature + 0.2)))
  {
    settingsStruct.SetterWindow -= 2.0;
  }
  else if ((settingsStruct.SetterTemperatureAverage > (SetterTargetTemperature + 0.1)))
  {
    settingsStruct.SetterWindow -= 1.0;
  }
  else if (settingsStruct.SetterTemperatureAverage < (SetterTargetTemperature - 0.2))
  {
    settingsStruct.SetterWindow += 2.0;
  }
  else if (settingsStruct.SetterTemperatureAverage < (SetterTargetTemperature - 0.1))
  {
    settingsStruct.SetterWindow += 1.0;
  }
}

void SetterPID() {
  mySetterPID.SetOutputLimits(settingsStruct.SetterMinWindow, settingsStruct.SetterMaxWindow);
  mySetterPID.SetTunings(settingsStruct.SetterKp, settingsStruct.SetterKi, settingsStruct.SetterKd);
  mySetterPID.Compute();
}

void SetterOff() {
  settingsStruct.SetterWindow = 0;
  digitalWrite(SetterPinSSRTemperature, LOW);
}

void SetterReadEssentialSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - SetterSensorEssentialTimer >= interval)
  {
    if (Debug) Serial.println("Checking setter sensors");
    SetterSensorEssentialTimer = millis(); //reset timer
      if (Simulator) {
          if (Debug) Serial.println("Using random values setter essential sensors");
          settingsStruct.SetterDS2Temperature = random(370, 380) / 10.0;
      } else {
          if (Debug) Serial.println("Using real values setter essential sensors");
          SetterDS1.requestTemperatures();
          double SetterTemperatureReading = SetterDS1.getTempCByIndex(0);
          if (isnan(SetterTemperatureReading))
            {
              if (Debug) Serial.println("Setter DHT error");
              settingsStruct.SetterErrorCount += 1;
              SetterTemperatureReading = settingsStruct.SetterDS2Temperature; // BACKUP
              //return; return statement takes it back
            }
          else {
            settingsStruct.SetterDS1Temperature = SetterTemperatureReading;       
            }
          SetterTempTotal = SetterTempTotal - SetterReadings[SetterTempReadIndex];// subtract the last reading:
          SetterReadings[SetterTempReadIndex] = SetterTemperatureReading;// read from the sensor:    
          SetterTempTotal = SetterTempTotal + SetterReadings[SetterTempReadIndex];// add the reading to the total:
          SetterTempReadIndex = SetterTempReadIndex + 1;// advance to the next position in the array:
          if (SetterTempReadIndex >= numReadings) {
            // ...wrap around to the beginning:
            SetterTempReadIndex = 0;
          }
          settingsStruct.SetterTemperatureAverage = SetterTempTotal / numReadings;// calculate the average:
      }
  }
}

void SetterReadSensors(unsigned long interval) {
  //Read all sensors in the setter
  if (millis() - SetterSensorTimer >= interval)
  {
    if (Debug) Serial.println("Checking setter sensors");
    SetterSensorTimer = millis(); //reset timer
      if (Simulator) {
          if (Debug) Serial.println("Using random values setter sensors");
          settingsStruct.SetterSCD30Temperature = random(370, 380) / 10.0;
          settingsStruct.SetterSCD30Humidity = random(400, 500) / 10.0;
          settingsStruct.SetterSCD30CO2 = random(500, 5000);
          settingsStruct.SetterDHTTemperature = random(370, 380) / 10.0;
          settingsStruct.SetterDHTHumidity = random(400, 500) / 10.0;
          settingsStruct.SetterDS2Temperature = random(370, 380) / 10.0;
          settingsStruct.HatcherDS1Temperature = random(370, 380) / 10.0;
          settingsStruct.SetterWindow = settingsStructRX.SetterMaxWindow;
      } else {
          if (Debug) Serial.println("Using real values setter sensors");
          double SetterTemperatureReading =  SetterDHT.readTemperature();
          double SetterHumidityReading = SetterDHT.readTemperature();
          if (isnan(SetterTemperatureReading))
            {
              if (Debug) Serial.println("Setter DHT error");
              settingsStruct.SetterErrorCount += 1;
            }
          else {
            settingsStruct.SetterDHTTemperature = SetterTemperatureReading;
            settingsStruct.SetterDHTHumidity = SetterHumidityReading;      
            }
          SetterDS2.requestTemperatures();
          settingsStruct.SetterDS2Temperature = SetterDS2.getTempCByIndex(0);          
          HatcherDS1.requestTemperatures();
          settingsStruct.HatcherDS1Temperature = HatcherDS1.getTempCByIndex(0); 
          scd30.read();
          settingsStruct.SetterSCD30Temperature = scd30.temperature;
          settingsStruct.SetterSCD30Humidity = scd30.relative_humidity;
          settingsStruct.SetterSCD30CO2 = scd30.CO2;
      }
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
    digitalWrite(SetterPinSSREggTurner, HIGH);
    delay(3000); //2.5 rpm at 50 Hz -> 12 sec for half turn
    digitalWrite(SetterPinSSREggTurner, LOW);
  }
}

void SetterPWM(unsigned long interval) {
  settingsStruct.SetterWindow = min(settingsStruct.SetterWindow, settingsStruct.SetterMaxWindow);
  settingsStruct.SetterWindow = max(settingsStruct.SetterWindow, settingsStruct.SetterMinWindow);
  if (millis() - SetterWindowTimer >= interval)
  { //time to shift the Relay Window
    if (Debug) Serial.println("Checking setter window");
    SetterWindowTimer += interval;
  }
  if (settingsStruct.SetterWindow > millis() - SetterWindowTimer) digitalWrite(SetterPinSSRTemperature, HIGH);
  else digitalWrite(SetterPinSSRTemperature, LOW);
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
