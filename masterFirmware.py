import time
from arduino import micros, delayMicros
from enum import Enum
import firmware


def playHandler(state, tile):
    tile.log("Play!")

def bottomInterruptHandler(state, tile):
    tile.log("received bottom pulse!")

def init(state, tile):
    tile.log("initializing")
    tile.bottom.registerInterruptHandler(lambda: bottomInterruptHandler(state, tile))
    tile.registerPlayHandler(lambda: playHandler(state, tile))

    state.tiles = []
    state.ready_to_report = True

def loop(state, tile):
    firmware.sendPulse(tile.bottom)
    tile.sleep()
    return
