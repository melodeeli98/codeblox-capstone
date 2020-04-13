#include "LowPower.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
//#include <functional-vlpp.h>
//#include "min_heap.h"
#include "side.h"
#include <avr/io.h>
using namespace std;
//using namespace vl;

void resetClock();

void initDriver(void (*callback)(Side_Name)){
  // turn off reflective sensors asap
  DDRB |= 1 << PINB7;
  PORTB |= 1 << PINB7;

  resetClock();

  //select external reference
  analogReference(EXTERNAL);

  Serial.begin(9600);

  initSides(callback);
}

void goToSleep(){
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  resetClock();
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

const unsigned long sensorLoadTime = 1000UL;
const int sensorThreshold = 380;
unsigned int *sensors = NULL;
int * sensor0 = NULL;
int * sensor1 = NULL;
int * sensor2 = NULL;
int * sensor3 = NULL;
int * sensor4 = NULL;
int * sensor5 = NULL;
bool readSensors = false;
bool readSensorsRaw = false;
unsigned long readSensorsTime = 0;
unsigned long readSensorsRawTime = 0;

//MinHeap<unsigned long, Func<void()>> eventHeap;

void updateDriver(){

  updateSides();

  if(readSensorsTime < timeMicros() && readSensors){
    readSensors = false;
    unsigned int value = 0;
    serialLog("HELLO");
    for (int sensor = 0; sensor < numReflectiveSensors; sensor++)
    {
      serialLog(readReflectiveSensor(sensor));
      value |= (((unsigned int)!(readReflectiveSensor(sensor) < sensorThreshold)) << sensor);
      serialLog(value);
    }
    *sensors = value;
    if(!readSensorsRaw){
      PORTB |= 1 << PINB7;
    }
    serialLog(*sensors);
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
  /*
  while (!eventHeap.empty() && eventHeap.topKey() < timeMicros()){
    //serialLog("deq event");
    //serialLog("freeMemory()=");
    //serialLog(freeMemory());
    //serialLog(timeMicros());
    //serialLog(eventHeap.topKey());
    eventHeap.pop()();
  }*/

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



void readReflectiveSensorsLater(unsigned int *s){
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
size_t serialLog(unsigned char s , int i){
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
unsigned long startTime = 0UL;

void resetClock(){
  /*
  while (!eventHeap.empty())
  {
    eventHeap.pop();
    serialLog("dropping events on reset?");
  }
  */
  startTime = micros();
}

unsigned long timeMicros(){
  unsigned long currTime = micros();
  if (startTime > currTime)
  { //aka overflow
    return (maxTime - startTime) + 1UL + currTime;
  }
  return currTime - startTime;
}
/*
void waitMicrosThen(unsigned long us, Func<void()> callback){
  eventHeap.push(us + timeMicros(), callback);
  //serialLog("enq event");
  //serialLog("freeMemory()=");
  //serialLog(freeMemory());
  //serialLog(timeMicros());
}
*/

int interruptDepth = 0;
void disableInterrupts(){
  interruptDepth++;
}
void enableInterrupts(){
  interruptDepth--;
}
bool interruptsEnabled(){
  return interruptDepth == 0;
}
