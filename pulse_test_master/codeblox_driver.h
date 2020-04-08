#pragma once

#include <ArduinoSTL.h>
#include <functional-vlpp.h>

//IR comm stuff
#include "side.h"

extern unsigned long pulseWidth; // TODO remove me later!

void initDriver(void (*)(enum Side_Name));
void updateDriver();

//reflective sensor stuff
const int numReflectiveSensors = 6;
void readReflectiveSensorsThen(vl::Func<void(unsigned int)>);
void readReflectiveSensorRawThen(int sensor, vl::Func<void(int)>);

//fake interrupt disabling/enabling
void disableInterrupts();
void enableInterrupts();
bool interruptsEnabled();

//timing/scheduling
unsigned long timeMicros(); //use this instead of micros to avoid overflow
void waitMicrosThen(unsigned long us, vl::Func<void()>);

void goToSleepThen(vl::Func<void()>);

//void registerPlayHandler(Func<void(void)>);

// debugging functions
void serialLog(String s);
bool newSerialMessage();
String getSerialMessage();
