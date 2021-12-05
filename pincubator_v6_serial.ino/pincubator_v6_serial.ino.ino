#include "SerialTransfer.h"
#define BlinkerPin 41 //Blinker pin

SerialTransfer myTransfer;

bool Simulator = true;
int BlinkerSpeed; //Blinker speed
int ledState = LOW;


unsigned long BlinkerTimer = 0;
unsigned long RxTxTimer = 0;

// **************************************************************
// * RX TX
// **************************************************************

struct STRUCTRX {
  byte SetterOnOff = 1;
  byte HatcherOnOff = 0;
  byte SetterPIDOnOff = 0;
  byte HatcherPIDOnOff = 0;
  byte SetterManualOnOff = 1;
  byte HatcherManualOnOff = 0;
  double SetterKp = 0.0;
  double SetterKi = 0.0;
  double SetterKd = 0.0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double SetterTempWindow = 10000.0;
  double HatcherTempWindow = 0.0;
} settingsStructRX;

struct STRUCT {
  byte SetterOnOff = 1;
  byte HatcherOnOff = 0;
  byte SetterPIDOnOff = 0;
  byte HatcherPIDOnOff = 0;
  byte SetterManualOnOff = 1;
  byte HatcherManualOnOff = 0;
  double SetterKp = 0.0;
  double SetterKi = 0.0;
  double SetterKd = 0.0;
  double HatcherKp = 0.0;
  double HatcherKi = 0.0;
  double HatcherKd = 0.0;
  double SetterTempWindow = 5000.0;
  double HatcherTempWindow = 0.0;
  double SetterWindow = 10000.0;
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

void setup()
{
  Serial.begin(115200);
  myTransfer.begin(Serial);
  pinMode(BlinkerPin, OUTPUT);
}


void loop()
{
  ToggleBlink();
  SerialRxTx(10000);
}

void SerialRxTx(int interval) {
  if (millis() - RxTxTimer >= interval){
    RxTxTimer = millis();
    if(myTransfer.available())
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
  settingsStruct.SetterOnOff = settingsStructRX.SetterOnOff;
  settingsStruct.HatcherOnOff = settingsStructRX.HatcherOnOff;
  settingsStruct.SetterPIDOnOff = settingsStructRX.SetterPIDOnOff;
  settingsStruct.HatcherPIDOnOff = settingsStructRX.HatcherPIDOnOff;
  settingsStruct.SetterManualOnOff = settingsStructRX.SetterManualOnOff;
  settingsStruct.HatcherManualOnOff = settingsStructRX.HatcherManualOnOff;
  settingsStruct.SetterKp = settingsStructRX.SetterKp;
  settingsStruct.SetterKi = settingsStructRX.SetterKi;
  settingsStruct.SetterKd = settingsStructRX.SetterKd;
  settingsStruct.HatcherKp = settingsStructRX.HatcherKp;
  settingsStruct.HatcherKi = settingsStructRX.HatcherKi;
  settingsStruct.HatcherKd = settingsStructRX.HatcherKd;
  settingsStruct.SetterTempWindow = settingsStructRX.SetterTempWindow;
  settingsStruct.HatcherTempWindow = settingsStructRX.HatcherTempWindow;
  }


void ToggleBlink() {
  if (Simulator == true) {
    BlinkerSpeed = 100;
  } else {
    BlinkerSpeed = 1000;
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
