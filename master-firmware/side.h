#pragma once

enum Side_Name: byte
{
    top = 0,
    right = 1,
    bottom = 2,
    left = 3
};


#include "message.h"

String sideToString(Side_Name side);

void initSides(void (*callback)(const Message &, enum Side_Name));
void resetSides();
void updateSides();

//before going to sleep, you must call this
//to disable the timer interrupt
void putSidesToSleep();

void sendMessage(Side_Name s, const Message& m);
void stopSending(Side_Name s);
void beginTimeout();
