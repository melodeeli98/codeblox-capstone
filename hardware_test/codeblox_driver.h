#pragma once

#define __AVR_ATmega328P__
#include <Arduino.h>

const int numReflectiveSensors = 6;

enum Side_Name
{
    top,
    right,
    bottom,
    left
};

enum Side_Name opposite(enum Side_Name);
enum Side_Name sideFromString(String side);

void disableInterrupts();
void enableInterrupts();
bool interruptsEnabled();

void initSides(void (*callback)(enum Side_Name));
void updateSides();
void sendPulseThen(enum Side_Name, void (*callback)(void));
void flipTile();

void initDriver(void (*callback)(enum Side_Name));
void updateDriver();
//use this instead of micros to avoid overflow
unsigned long timeMicros();
void waitMicrosThen(unsigned long us, void (*callback)(void));
void readReflectiveSensorsThen(void (*callback)(unsigned int));
void readReflectiveSensorRawThen(int sensor, void (*callback)(int));
void goToSleepThen(void (*callback)(void));
//void registerPlayHandler(void (*callback)(void));
void serialLog(String s);
bool newSerialMessage();
String getSerialMessage();
