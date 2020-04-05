#define UBRR0H
#define __AVR__
#define __AVR_ATmega328P__
#include <Arduino.h>

#include "LowPower.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <list>
#include "min_heap.h"
#include <avr/io.h>
using namespace std;

void resetClock();

//Reflective Sensor Output
// PortB 7

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

void (*wakeupCallback)(void) = NULL;
void goToSleepThen(void (*callback)(void))
{
  wakeupCallback = callback;
}

//incoming
list<String> receivedMessages;

//outgoing
list<String> messagesToSend;

static MinHeap<unsigned long, void (*)()> eventHeap;

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

  if (wakeupCallback != NULL)
  {
    LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
    void (*callback)(void) = wakeupCallback;
    wakeupCallback = NULL;
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

void readReflectiveSensorsThen(void (*callback)(unsigned int))
{
  static void (*static_callback)(unsigned int) = NULL;
  static_callback = callback;
  PORTB &= ~(1 << PINB7);
  waitMicrosThen(sensorLoadTime, []() {
    unsigned int value = 0;
    for (int sensor = 0; sensor < numReflectiveSensors; sensor++)
    {
      value |=
          (((unsigned int)!(readReflectiveSensor(sensor) <
                            sensorThreshold))
           << sensor);
    }
    PORTB |= 1 << PINB7;
    static_callback(value);
  });
}

void readReflectiveSensorRawThen(int sensor, void (*callback)(int))
{
  static void (*static_callback)(int) = NULL;
  static_callback = callback;
  static int static_sensor = 0;
  static_sensor = sensor;

  PORTB &= ~(1 << PINB7);
  waitMicrosThen(sensorLoadTime, []() {
    int value = readReflectiveSensor(static_sensor);
    PORTB |= 1 << PINB7;
    static_callback(value);
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

String
getSerialMessage()
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

void waitMicrosThen(unsigned long us, void (*callback)(void))
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
  return interruptDepth > 0;
}
