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
#define VCHatcherKp 32


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
long SetterDHTErrorCount;
long HatcherExtDHTErrorCount;
long HatcherIntDHTErrorCount;

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
unsigned long LastSerialPush;

unsigned long SetterLastSensorCheck;
unsigned long SetterLastEggTurnCheck;
unsigned long SetterLastTemperatureTargetCheck;
unsigned long SetterLastCozirCheck;

unsigned long HatcherLastOnOffCheck;
unsigned long HatcherLastSensorCheck;
unsigned long HatcherLastTemperatureTargetCheck;
unsigned long HatcherLastCozirCheck;

unsigned long windowStartTime;
// 10 second Time Proportional Output window
int SetterWindowLastCheck = 10000;
int HatcherWindowLastCheck = 10000;


//Initialize COZIR
SoftwareSerial Hatchersws(HatcherPinCozir1, HatcherPinCozir2);
COZIR Hatcherczr(&Hatchersws);

//Initialize COZIR
//SoftwareSerial swsSetter(PinSetterCozir1, PinSetterCozir2);
//COZIR Setterczr(&swsSetter);

//Virtual switches
int SetterOnOff, HatcherOnOff, SetterManualOnOff, HatcherManualOnOff, SetterPIDOnOff, HatcherPIDOnOff;

// ************************************************
// PID Variables and constants
// ************************************************

//Define Variables we'll be connecting to
//Kp=0.45*maxwindowsize
double SetterKp; 
double SetterNewK;
double SetterKi;
double SetterKd;
double SetterWindow;
double SetterTempWindow;

double HatcherKp, HatcherNewK, HatcherKi, HatcherKd;
int HatcherWindow, HatcherTempWindow;

//Specify the links and initial tuning parameters
PID mySetterPID(&SetterTempAverage, &SetterWindow, &SetterTargetTemperature, SetterKp, SetterKi, SetterKd, DIRECT);
//PID myHatcherPID(&HatcherTemperature, &HatcherOutput, &HatcherTargetTemperature, &HatcherKp, &HatcherKi, &HatcherKd, DIRECT);




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

  // Initialize Pins so relays are inactive at reset
  digitalWrite(PinRelayUnused6, RelayOFF);
  digitalWrite(PinRelayUnused7, RelayOFF);
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(SetterPinRelayEggTurner, RelayOFF);
  digitalWrite(SetterPinSSRTemperature, LOW);
  digitalWrite(HatcherPinSSRTemperature, LOW);

  // **************************************************************
  // * TIMERS
  // ***************************************************************/
  windowStartTime = millis();
  LastSerialPush = millis();
  SetterLastSensorCheck = millis() + sec(5);
  SetterLastEggTurnCheck = millis();
  SetterLastTemperatureTargetCheck = millis();
  HatcherLastOnOffCheck = millis();
  HatcherLastSensorCheck = millis() + sec(5);
  HatcherLastCozirCheck = millis() + sec(5);
  HatcherLastTemperatureTargetCheck = millis();


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
  SetterKp = 0.1;
  SetterKi = 3.0;
  SetterKd = 0.2;
  SetterWindow = 1000;
  SetterTempWindow = 1000;

  HatcherKp = 0.1;
  HatcherKi = 3.0;
  HatcherKd = 0.2;
  HatcherWindow = 1000;
  HatcherTempWindow = 1000;
  
  mySetterPID.SetMode(AUTOMATIC);
  mySetterPID.SetOutputLimits(300, 1000);
  //myPID.SetSampleTime(60000);
  //tell the PID to range between 0 and the full window size

  // **************************************************************
  // * SET TEMPERATURE TARGET
  // ***************************************************************/
  HatcherTargetExtTemperature = 40.1;

  // **************************************************************
  // * ERROR COUNTERS
  // ***************************************************************/
  SetterDHTErrorCount = 0;
  HatcherIntDHTErrorCount = 0;
  HatcherExtDHTErrorCount = 0;
  
  // **************************************************************
  // * VIRTUAL SWITCHES
  // ***************************************************************/
  SetterOnOff = 1;
  HatcherOnOff = 1;
  //PushNotificationsOnOff = 0;
  SetterPIDOnOff = 0;
  HatcherPIDOnOff = 0;

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
  //Baud rate can be specified by calling Cayenne.begin(username, password, clientID, 9600);
  Serial.begin(9600);
  //SendMessage("Pincubator started", "Success", "0");
  digitalWrite(PinRelayUnused6, RelayON);
  delay(1000);
  digitalWrite(PinRelayUnused6, RelayOFF); 
}

void loop() {
  
  SerialSendReceive(1000);
  
  if (SetterOnOff == 0) SetterOff(); else SetterOn();

  if (HatcherOnOff == 0) HatcherOff();
  else HatcherOn();
}

void SetterOn() {
  
  //SetterReadSensors(10000); // every 10 seconds
  
  SetterEggTurn(3600000); //every hour
  SetterSimulator();  
  if (SetterManualOnOff == 1) SetterManualMode();
  else {
      if (SetterPIDOnOff == 0) SetterAutomaticMode(60000, false);
      else SetterAutomaticMode(60000, true);
      }
  SetterPWM(SetterWindow);

}
void SetterOff() {
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(SetterPinSSRTemperature, LOW);
}
void SetterSimulator() {
  SetterTempAverage = random(1, 500) / 100.0;
  SetterHumidity = random(1, 500) / 100.0;
  SetterCozirTemperature = random(1, 500) / 100.0;
  SetterCozirHumidity = random(1, 500) / 100.0;
  SetterCozirCO2 = random(1, 500) / 100.0;
  SetterKp = random(1, 500) / 100.0;
  SetterKi = random(1, 500) / 100.0;
  SetterKd= random(1, 500) / 100.0;
}
void SerialSendReceive(int interval) {
  //Read all sensors in the setter
  if (millis() - LastSerialPush > interval)
  {
    LastSerialPush = millis();
    //Receive
    int size_ = 0;
    //String  payload;
    //while ( !Serial.available()  ){}
    //  if ( Serial.available() )
    String payload = Serial.readStringUntil( '\n' );
    StaticJsonDocument<512> InDoc;
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
        SetterTempWindow = InDoc["SetterWindow"].as<unsigned long>();
        HatcherTempWindow = InDoc["HatcherWindow"].as<unsigned long>();        
        SetterPIDOnOff = InDoc["SetterPIDOnOff"].as<unsigned long>();
        HatcherPIDOnOff = InDoc["HatcherPIDOnOff"].as<unsigned long>();       
        SetterKp = InDoc["SetterKp"].as<double>();  
        SetterKi = InDoc["SetterKi"].as<double>(); 
        SetterKd = InDoc["SetterKd"].as<double>(); 
        HatcherKp = InDoc["HatcherKp"].as<double>(); 
        HatcherKi = InDoc["HatcherKi"].as<double>(); 
        HatcherKd = InDoc["HatcherKd"].as<double>(); 
    }

    //Send v2
    StaticJsonDocument<512> OutDoc;
    OutDoc["TimeOn"] = String(millis()/1000);
    OutDoc["SetterOnOff"] = String(SetterOnOff);
    OutDoc["HatcherOnOff"] = String(HatcherOnOff);
    OutDoc["SetterWindow"] = String(SetterWindow);
    OutDoc["HatcherWindow"] = String(HatcherWindow);
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

    digitalWrite(PinRelayUnused7, RelayON);
    delay(100);
    digitalWrite(PinRelayUnused7, RelayOFF);
  }
  
}
void SetterReadSensors(int interval) {
  //Read all sensors in the setter
  if (millis() - SetterLastSensorCheck > interval)
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
  if (millis() - SetterLastEggTurnCheck > interval)
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
  if (millis() - SetterLastTemperatureTargetCheck > interval)
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
  //Turn the output pin on/off based on pid output
  if (millis() - SetterWindowLastCheck > interval)
  { //time to shift the Relay Window
    SetterWindowLastCheck = millis();
    if (digitalRead(SetterPinSSRTemperature) == HIGH) {
          digitalWrite(SetterPinSSRTemperature, HIGH);
    }  else digitalWrite(SetterPinSSRTemperature, LOW); 
  }
}


void HatcherOn() {
  HatcherSimulator();
  //ReadHatcherSensors();
  //HatcherTemperatureCheck();
  //HatcherHumidityCheck();
  //HatcherSetpointCheck();
}
void HatcherOff() {
  //SHUT DOWN HATCHER ENTIRELY
  digitalWrite(HatcherPinRelayHumidity, RelayOFF);
  digitalWrite(HatcherPinSSRTemperature, LOW);
}
void HatcherSimulator() {

  HatcherIntTempAverage = random(1, 500) / 100.0;
  HatcherIntHumidity = random(1, 500) / 100.0;
  HatcherCozirTemperature = random(1, 500) / 100.0;
  HatcherCozirHumidity = random(1, 500) / 100.0;
  HatcherCozirCO2 = random(1, 500) / 100.0;
  HatcherKp = random(1, 500) / 100.0;
  HatcherKi = random(1, 500) / 100.0;
  HatcherKd = random(1, 500) / 100.0;
}
void HatcherReadSensors(int interval) {
  //Read all sensors in the setter
  if (millis() - HatcherLastSensorCheck > interval)
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
void HatcherSetpointCheck() {
  /************************************************
    HATCHER SETPOINT ADJUSTMENT
  ************************************************/
  if (millis() - HatcherLastTemperatureTargetCheck > 900000)
  { //time to shift the temperature set 0.2 down or 0.1 up each 15 minutes
    HatcherLastTemperatureTargetCheck =  millis();
    if (HatcherIntTemperature > HatcherTargetIntTemperature + 0.3) HatcherTargetExtTemperature -= 0.5;
    else if (HatcherIntTemperature < HatcherTargetIntTemperature - 0.3) HatcherTargetExtTemperature += 0.1;
  }
}
int sec(int s) {
  int result;
  result = s * 1000;
  return result;
}
void ShortBlinker(int times) {
  for(int i = 0; i <= times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(100);                       // wait for a second
    digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
    delay(100);
  } 
}
void LongBlinker(int times) {
  for(int i = 0; i <= times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(1000);                       // wait for a second
    digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
    delay(1000);
  } 
}


