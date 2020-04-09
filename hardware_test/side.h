#pragma once

#include <functional-vlpp.h>

enum Side_Name
{
    top,
    right,
    bottom,
    left
};

enum Side_Name opposite(enum Side_Name);
enum Side_Name sideFromString(String side);
String sideToString(Side_Name side);

void initSides(vl::Func<void(enum Side_Name)>);

void updateSides();

void sendPulseThen(enum Side_Name, vl::Func<void(void)>);

void flipTile();
