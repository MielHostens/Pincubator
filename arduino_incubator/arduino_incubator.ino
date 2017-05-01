
/* How to use the DHT-22 sensor with Arduino uno
   Temperature and humidity sensor
*/

//Libraries
#include <DHT.h>
#include <Arduino.h>
#include <cozir.h>
#include <SoftwareSerial.h>

// Constants for Arduino relay board
#define RELAY_ON 0
#define RELAY_OFF 1

//Constants for DHT sensors
#define DHTPIN_EXT 2     // what pin is connected to the outside temperature room (OUT)
#define DHTPIN_INT 3     // what pin is connected to the inside temperature room (IN)
#define DHTTYPE DHT22   // DHT 22  (AM2302)

//Constants for Arduino relay board switches
#define RELAYPIN_HEAT 7
#define RELAYPIN_VENT_HEAT 6
#define RELAYPIN_HUM 8
#define RELAYPIN_TURN 9
#define RELAYPIN_VENT 12


DHT dht_ext(DHTPIN_EXT, DHTTYPE); //// Initialize DHT sensor EXT for normal 16mhz Arduino
DHT dht_int(DHTPIN_INT, DHTTYPE); //// Initialize DHT sensor INT for normal 16mhz Arduino


//Variables
int chk;
float hum_int;  //Stores internal humidity value
float temp_int; //Stores internal temperature value
float hum_ext;  //Stores external humidity value
float temp_ext; //Stores external temperature value

//Cozir 
float temp_cozir;
float hum_cozir;
int c_cozir;
int digi_cozir;


// temperature settings
double temp_ext_set;  //Setting external temperature value
double temp_int_set;  //Stores internal humidity value
double hum_int_set; //Stores internal temperature value


//Specifiy window sizes for sensors
long TempWindowSize = 900000;
unsigned long TempwindowStartTime;

int HumWindowSize = 5000;
unsigned long HumwindowStartTime;

long TurnWindowSize = 3600000;
unsigned long TurnwindowStartTime;

long VentWindowSize = 3600000;
unsigned long VentwindowStartTime;

//Initialize COZIR
SoftwareSerial nss(10,11);
COZIR czr(nss);


void setup()
{
  //-------( Initialize Pins so relays are inactive at reset)----
  digitalWrite(RELAYPIN_HEAT, RELAY_OFF);
  digitalWrite(RELAYPIN_VENT_HEAT, RELAY_OFF);
  digitalWrite(RELAYPIN_HUM, RELAY_OFF);
  digitalWrite(RELAYPIN_TURN, RELAY_OFF);
  digitalWrite(RELAYPIN_VENT, RELAY_OFF);
  digitalWrite(13, RELAY_OFF);

  //---( THEN set pins as outputs )----
  pinMode(RELAYPIN_HEAT, OUTPUT);    
  pinMode(RELAYPIN_VENT_HEAT, OUTPUT);    
  pinMode(RELAYPIN_HUM, OUTPUT);  
  pinMode(RELAYPIN_TURN, OUTPUT);  
  pinMode(RELAYPIN_VENT, OUTPUT);  

  //--- ( ALWAYS VENT EXTERNAL CHAMBER)
  digitalWrite(RELAYPIN_VENT_HEAT, RELAY_OFF);

  TempwindowStartTime = millis();
  HumwindowStartTime = millis();
  TurnwindowStartTime = millis();
  VentwindowStartTime = millis();
        
  //initialize the variables we're linked to
  temp_ext_set = 39.6;
  temp_int_set = 37.8;
  hum_int_set = 55;
  

  //start serial signaling
  Serial.begin(9600);
  //turn DHT sensors on
  dht_ext.begin();
  dht_int.begin();
  //turn Cozir sensors on
  delay(5000);
  //czr.SetOperatingMode(CZR_POLLING);
  //czr.SetOperatingMode(CZR_STREAMING);
  //czr.CalibrateFreshAir();
  //czr.SetDigiFilter(64);
}

void loop()
{
    delay(4000);
    //Read data and store it to variables hum and temp
    hum_ext = dht_ext.readHumidity();
    temp_ext= dht_ext.readTemperature();
    hum_int = dht_int.readHumidity();
    temp_int= dht_int.readTemperature();
    temp_cozir = czr.Celsius();
    hum_cozir = czr.Humidity();
    c_cozir = czr.CO2();
    digi_cozir = czr.GetDigiFilter();
    //Print temp and humidity values to serial monitor
    Serial.print("Hum int: ");
    Serial.print(hum_int);
    Serial.print("%, Temp int: ");
    Serial.print(temp_int);
    Serial.print("°C, Hum ext: ");
    Serial.print(hum_ext);
    Serial.print("%, Temp ext: ");
    Serial.print(temp_ext);
    Serial.print("°C, Temp extset: ");
    Serial.print(temp_ext_set);
    Serial.print("°C, Cozir temp : ");
    Serial.print(temp_cozir);
    Serial.print("°C, Cozir hum : ");
    Serial.print(hum_cozir);
    Serial.print("%, Cozir CO2 : ");
    Serial.print(c_cozir);
    Serial.print("PPM, Cozir DF : ");
    Serial.print(digi_cozir);
      
    /**************************************************************
    * turn the temperature output pin on/off based on pid output
    ***************************************************************/
    unsigned long now = millis();
    Serial.print(", TTNT: ");
    Serial.println(now - TempwindowStartTime);

      
    if(temp_ext > temp_ext_set) 
      {
        digitalWrite(RELAYPIN_HEAT,RELAY_OFF);
      }
    else if (temp_int < temp_ext_set - 0.2)
      {
        digitalWrite(RELAYPIN_HEAT,RELAY_ON);
      }
    
    //HUMIDITY
    
    /************************************************************
    * turn the humidity output pin on/off based on pid output   
    *************************************************************/
    if(hum_int > 55)
    {
      digitalWrite(RELAYPIN_HUM,RELAY_OFF);
    }
    else if (hum_int < 50)
    {
      digitalWrite(RELAYPIN_HUM,RELAY_ON);
    }
    
    //TEMPERATURE ADJUSTMENT
    
    /************************************************
    * turn the exteral temperature setpoint 
    ************************************************/
    
    if(now - TempwindowStartTime>TempWindowSize)
    { //time to shift the temperature set one decimal down
      TempwindowStartTime += TempWindowSize;
       if(temp_int > temp_int_set) 
       {
         temp_ext_set -=0.1;
        }
    }  
    
    
    //TURNING
    
    /************************************************
    * turn the turning output pin on/off
    ************************************************/
    
    if(now - TurnwindowStartTime>TurnWindowSize)
    { //time to shift the Relay Window
      TurnwindowStartTime += TurnWindowSize;
      digitalWrite(RELAYPIN_TURN,RELAY_ON);
      delay(14000);
      digitalWrite(RELAYPIN_TURN,RELAY_OFF);
      Serial.print("Turning the eggs");
    }
    
    
    //VENTILATION
    /************************************************
    * turn the turning output pin on/off
    ************************************************/
    //
    //if(now - VentwindowStartTime>VentWindowSize)
    //{ //time to shift the Relay Window
    //  VentwindowStartTime += VentWindowSize;
    //  digitalWrite(RELAYPIN_VENT,RELAY_ON);
    //  delay(5000);
    //  digitalWrite(RELAYPIN_VENT,RELAY_OFF);
    //}
  
  
}
