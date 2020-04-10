#pragma once

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

void initSides(void (*)(enum Side_Name));

void updateSides();

void sendPulse(enum Side_Name);

void flipTile();
