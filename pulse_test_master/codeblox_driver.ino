#include "LowPower.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>
#include <list>
#include "min_heap.h"
#include "side.h"
#include <avr/io.h>
using namespace std;
using namespace vl;

void resetClock();

void initDriver(void (*callback)(Side_Name))
{
  // turn off reflective sensors asap
  DDRB |= 1 << PINB7;
  PORTB |= 1 << PINB7;

  resetClock();

  //select external reference
  analogReference(EXTERNAL);

  Serial.begin(9600);

  initSides(callback);
}

Func<void()> wakeupCallback;
bool timeToSleep = false;
void goToSleepThen(Func<void()> callback)
{
  wakeupCallback = callback;
  timeToSleep = true;
}

//incoming
list<String> receivedMessages;

//outgoing
list<String> messagesToSend;

MinHeap<unsigned long, Func<void()>> eventHeap;

void updateDriver()
{

  updateSides();

  while (!eventHeap.empty() && eventHeap.topKey() < timeMicros())
  {
    eventHeap.pop()();
  }

  //read new messages
  static String nextMessage = "";
  while (Serial.available() > 0)
  {
    // read the incoming byte:
    char incomingByte = (char)Serial.read();
    if (incomingByte == '\n')
    {
      receivedMessages.push_back(nextMessage);
      nextMessage = "";
    }
    else
    {
      nextMessage += incomingByte;
    }
  }

  if (timeToSleep)
  {
    LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
    Func<void()> callback = wakeupCallback;
    timeToSleep = false;
    wakeupCallback = [](){};
    resetClock();
    callback();
  }

  if (!messagesToSend.empty())
  {
    Serial.println(messagesToSend.back().c_str());
    messagesToSend.pop_back();
  }
}

int readReflectiveSensor(int sensor)
{
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

void readReflectiveSensorsThen(Func<void(unsigned int)> callback)
{
  PORTB &= ~(1 << PINB7);
  waitMicrosThen(sensorLoadTime, [callback]() {
    unsigned int value = 0;
    for (int sensor = 0; sensor < numReflectiveSensors; sensor++)
    {
      value |= (((unsigned int)!(readReflectiveSensor(sensor) < sensorThreshold)) << sensor);
    }
    PORTB |= 1 << PINB7;
    callback(value);
  });
}

void readReflectiveSensorRawThen(int sensor, Func<void(int)> callback)
{
  PORTB &= ~(1 << PINB7); 
  waitMicrosThen(sensorLoadTime, [sensor, callback]() {
    int value = readReflectiveSensor(sensor);
    PORTB |= 1 << PINB7;
    callback(value);
  });
}

void serialLog(String s)
{
  messagesToSend.push_front(s);
}

bool newSerialMessage()
{
  return !receivedMessages.empty();
}

String getSerialMessage()
{
  String s = receivedMessages.front();
  receivedMessages.pop_front();
  return s;
}

const unsigned long maxTime = ~0UL;
unsigned long startTime = 0UL;

void resetClock()
{
  while (!eventHeap.empty())
  {
    eventHeap.pop();
    serialLog("dropping events on reset?");
  }
  startTime = micros();
}

unsigned long
timeMicros()
{
  unsigned long currTime = micros();
  if (startTime > currTime)
  { //aka overflow
    return (maxTime - startTime) + 1UL + currTime;
  }
  return currTime - startTime;
}

void waitMicrosThen(unsigned long us, Func<void()> callback)
{
  eventHeap.push(us + timeMicros(), callback);
}

int interruptDepth = 0;
void disableInterrupts()
{
  interruptDepth++;
}

void enableInterrupts()
{
  interruptDepth--;
}

bool interruptsEnabled()
{
  return interruptDepth == 0;
}
