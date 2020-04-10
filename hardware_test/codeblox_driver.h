#pragma once
//#include <functional-vlpp.h>

//IR comm stuff
#include "side.h"

void initDriver(void (*)(enum Side_Name));
void updateDriver();

const int numReflectiveSensors = 6;

void readReflectiveSensorsLater(unsigned int *);
void readReflectiveSensorsRawLater(int *, int *, int *, int *, int *, int *);

//fake interrupt disabling/enabling
void disableInterrupts();
void enableInterrupts();
bool interruptsEnabled();

//timing/scheduling
unsigned long timeMicros(); //use this instead of micros to avoid overflow
//void waitMicrosThen(unsigned long us, vl::Func<void()>);

void goToSleep();

//void registerPlayHandler(Func<void(void)>);

void listenForSerialMessages(void (*callback)(char *));

size_t serialLog(const __FlashStringHelper * );
size_t serialLog(const String &s);
size_t serialLog(const char[]);
size_t serialLog(char);
size_t serialLog(unsigned char , int = DEC);
size_t serialLog(int, int = DEC);
size_t serialLog(unsigned int, int = DEC);
size_t serialLog(long, int = DEC);
size_t serialLog(unsigned long, int = DEC);
size_t serialLog(double, int = 2);
size_t serialLog(const Printable& s);
size_t serialLog(void);

