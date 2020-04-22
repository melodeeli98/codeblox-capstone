#pragma once

enum Side_Name: byte
{
    top = 1,
    right = 2,
    bottom = 3,
    left = 4
};


#include "message.h"

String sideToString(Side_Name side);

void initSides(void (*callback)(const Message &, enum Side_Name));

void updateSides();

void startCommAllSides();
void stopComm(Side_Name);
bool isValid(Side_Name side_name);

//before going to sleep, you must call this
//to disable the timer interrupt
void stopSendTimer();

int numAvailableWords(Side_Name);

byte peekWord(Side_Name);

byte popWord(Side_Name);

void sendMessage(Side_Name s, const Message& m);

