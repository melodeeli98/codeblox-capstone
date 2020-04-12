#pragma once

enum Side_Name: unsigned int
{
    top = 1,
    right = 2,
    bottom = 3,
    left = 4
};

enum Side_Name opposite(enum Side_Name);
enum Side_Name sideFromString(String side);
String sideToString(Side_Name side);

void initSides(void (*)(enum Side_Name));

void updateSides();

void sendPulse(enum Side_Name);

void flipTile();
