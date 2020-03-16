import time
from arduino import micros, delayMicros
from enum import Enum
import firmware
from firmware import SideStateMachine, CLOCK_PERIOD, Message


def playHandler(state, tile):
    tile.log("Play!")
    state.sides["bottom"].enqueueMessage(Message(False, [firmware.WAKE_UP]))
    state.sides["bottom"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_TOP]))


def bottomInterruptHandler(state, tile):
    tile.log("received bottom pulse!")


def init(state, tile):
    tile.log("initializing")
    tile.bottom.registerInterruptHandler(
        lambda: bottomInterruptHandler(state, tile))
    tile.registerPlayHandler(lambda: playHandler(state, tile))

    state.tiles = []
    state.ready_to_report = True

    state.sides = {"bottom": SideStateMachine()}

    tile.sleep()


def loop(state, tile):
    bit = state.sides["bottom"].getNextBitToSend()
    if bit > 0:
        firmware.sendPulse(tile.bottom)
    delayMicros(CLOCK_PERIOD)
    return
