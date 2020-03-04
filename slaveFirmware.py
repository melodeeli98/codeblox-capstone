import time
from arduino import micros, delayMicros
from enum import Enum
import firmware


def topInterruptHandler(state, tile):
    tile.log("received top pulse!")
    pass


def leftInterruptHandler(state, tile):
    tile.log("received left pulse!")
    pass


def rightInterruptHandler(state, tile):
    tile.log("received right pulse!")
    pass


def bottomInterruptHandler(state, tile):
    tile.log("received bottom pulse!")
    pass


def init(state, tile):
    tile.log("initializing")
    tile.top.registerInterruptHandler(lambda: topInterruptHandler(state, tile))
    tile.left.registerInterruptHandler(lambda: leftInterruptHandler(state, tile))
    tile.right.registerInterruptHandler(lambda: rightInterruptHandler(state, tile))
    tile.bottom.registerInterruptHandler(lambda: bottomInterruptHandler(state, tile))

    state.tiles = []
    state.ready_to_report = False
    


def loop(state, tile):
    tile.sleep()
    return
