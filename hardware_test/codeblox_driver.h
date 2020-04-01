#pragma once

const int numReflectiveSensors = 6;

enum Side_Name {top, right, bottom, left};

Side_Name opposite(Side_Name);
Side_Name sideFromString(String side);

void disableInterrupts();
void enableInterrupts();
bool interruptsEnabled();

static void initSides(void (*callback)(Side_Name));
void updateSides();
void sendPulseThen(Side_Name, void (*callback)(void));
void flipTile();

void initDriver(void (*callback)(Side_Name));
void updateDriver();
void waitMicrosThen(unsigned long us, void (*callback)(void));
void readReflectiveSensorsThen(void (*callback)(int));
void readReflectiveSensorRawThen(int sensor, void (*callback)(int));
void goToSleepThen(void (*callback)(void));
void registerPlayHandler(void (*callback)(void));
void serialLog(String s);
bool newSerialMessage();
String getSerialMessage();


