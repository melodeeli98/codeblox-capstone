#include "LowPower.h"
#include "codeblox_driver.h"
#include "side.h"
#include <avr/io.h>

void resetClock();

void initDriver(void (*newMessageCallback)(const Message&, enum Side_Name)){
  // turn off reflective sensors asap
  DDRB |= 1 << PINB7;
  PORTB |= 1 << PINB7;

  resetClock();

  //select external reference
  analogReference(EXTERNAL);

  Serial.begin(9600);
  delay(10);
  
  initSides(newMessageCallback);
}

void goToSleep(){
  putSidesToSleep();
  //Serial.println("sleeping");
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  //Serial.println("awake");
}

void (*newSerialMessageCallback)(char *) = NULL;

void registerSerialMessageCallback(void (*callback)(char *)){
  newSerialMessageCallback = callback;
}

int readReflectiveSensor(int sensor){
  switch (sensor)
  {
  case 0:
    return analogRead(A0);
  case 1:
    return analogRead(A1);
  case 2:
    return analogRead(A2);
  case 3:
    return analogRead(A3);
  case 4:
    return analogRead(A4);
  case 5:
    return analogRead(A5);
  default:
    return 0;
  }
}

static const unsigned long sensorLoadTime = 1000UL;
static const int sensorThreshold = 250;
static volatile byte * sensors = NULL;
static volatile int * sensor0 = NULL;
static volatile int * sensor1 = NULL;
static volatile int * sensor2 = NULL;
static volatile int * sensor3 = NULL;
static volatile int * sensor4 = NULL;
static volatile int * sensor5 = NULL;
static volatile bool readSensors = false;
static volatile bool readSensorsRaw = false;
static volatile unsigned long readSensorsTime = 0;
static volatile unsigned long readSensorsRawTime = 0;


void updateDriver(){
  updateSides();

  if(readSensorsTime < timeMicros() && readSensors){
    readSensors = false;
    byte value = 0;
    for (int sensor = 0; sensor < numReflectiveSensors; sensor++)
    {
      value |= (((byte)!(readReflectiveSensor(sensor) < sensorThreshold)) << sensor);
    }
    *sensors = value;
    if(!readSensorsRaw){
      PORTB |= 1 << PINB7;
    }
  }

  if(readSensorsRawTime < timeMicros() && readSensorsRaw){
    readSensorsRaw = false;
    *sensor0 = readReflectiveSensor(0);
    *sensor1 = readReflectiveSensor(1);
    *sensor2 = readReflectiveSensor(2);
    *sensor3 = readReflectiveSensor(3);
    *sensor4 = readReflectiveSensor(4);
    *sensor5 = readReflectiveSensor(5);
    if(!readSensors){
      PORTB |= 1 << PINB7;
    }
  }


  //read incoming serial messages
  const unsigned int maxReceivedMessageSize = 20;
  static char receivedMessage[maxReceivedMessageSize] = "";
  static unsigned int messagePos = 0;
  while (Serial.available() > 0 && newSerialMessageCallback != NULL){
    // read the incoming byte:
    char incomingByte = (char)Serial.read();
    if (incomingByte == '\n')
    {
      newSerialMessageCallback(receivedMessage);
      receivedMessage[0] = '\0';
      messagePos = 0;
    }
    else
    {
      if(messagePos < maxReceivedMessageSize-1){
        receivedMessage[messagePos] = incomingByte;
        receivedMessage[messagePos+1] = '\0';
        messagePos++;
      }
    }
  }
}



void readReflectiveSensorsLater(byte *s){
  sensors = s;
  readSensors = true;
  readSensorsTime = timeMicros() + sensorLoadTime;
  PORTB &= ~(1 << PINB7);
}

void readReflectiveSensorsRawLater(int *s0, int *s1, int *s2, int *s3, int *s4, int *s5){
  sensor0 = s0;
  sensor1 = s1;
  sensor2 = s2;
  sensor3 = s3;
  sensor4 = s4;
  sensor5 = s5;
  readSensorsRaw = true;
  readSensorsRawTime = timeMicros() + sensorLoadTime;
  
  PORTB &= ~(1 << PINB7);
}


size_t serialLog(const __FlashStringHelper * s){
  return Serial.println(s);
}
size_t serialLog(const String &s){
  return Serial.println(s);
}
size_t serialLog(const char s[]){
  return Serial.println(s);
}
size_t serialLog(char s){
  return Serial.println(s);
}
size_t serialLog(byte s , int i){
  return Serial.println(s, i);
}
size_t serialLog(int s, int i){
  return Serial.println(s, i);
}
size_t serialLog(unsigned int s, int i){
  return Serial.println(s, i);
}
size_t serialLog(long s, int i){
  return Serial.println(s, i);
}
size_t serialLog(unsigned long s, int i){
  return Serial.println(s, i);
}
size_t serialLog(double s, int i){
  return Serial.println(s, i);
}
size_t serialLog(const Printable& s){
  return Serial.println(s);
}
size_t serialLog(void){
  return Serial.println();
}

const unsigned long maxTime = ~0UL;
volatile unsigned long startTime = 0UL;

void resetClock(){
  startTime = micros();
}

unsigned long timeMicros(){
  volatile unsigned long currTime = micros();
  if (startTime > currTime)
  { //aka overflow
    return (maxTime - startTime) + 1UL + currTime;
  }
  return currTime - startTime;
}

