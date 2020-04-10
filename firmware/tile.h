#pragma once

#include <boost/interprocess/managed_shared_memory.hpp>
#include "side.h"
#include "tile.h"

void run();
void kill();
void waitUntilDone();
void getTiles();

void serialLog(char *s);
