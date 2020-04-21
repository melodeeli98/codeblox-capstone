#pragma once

//IR comm stuff
#include "side.h"
#include "message.h"

void initDriver(void (*)(Message, enum Side_Name));
void updateDriver();

const int numReflectiveSensors = 6;

void readReflectiveSensorsLater(byte *);
void readReflectiveSensorsRawLater(int *, int *, int *, int *, int *, int *);

//timing/scheduling
unsigned long timeMicros(); //use this instead of micros to avoid overflow

void goToSleep();

void registerSerialMessageCallback(void (*callback)(char *));

//#define LOG(...) serialLog(__VA_ARGS__)
#define LOG(...) ((void)0)

size_t serialLog(const __FlashStringHelper * );
size_t serialLog(const String &s);
size_t serialLog(const char[]);
size_t serialLog(char);
size_t serialLog(byte , int = DEC);
size_t serialLog(int, int = DEC);
size_t serialLog(unsigned int, int = DEC);
size_t serialLog(long, int = DEC);
size_t serialLog(unsigned long, int = DEC);
size_t serialLog(double, int = 2);
size_t serialLog(const Printable& s);
size_t serialLog(void);

