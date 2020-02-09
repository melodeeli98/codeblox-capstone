import time
from arduino import micros

CLOCK_PERIOD = 50000  # 50ms


def leftClockCallback(state, tile):
    pass


def topClockCallback(state, tile):
    pass


def init(state, tile):
    tile.top.registerClockCallback(lambda: topClockCallback(state, tile))
    tile.left.registerClockCallback(lambda: leftClockCallback(state, tile))
    state.tiles = []
    state.ready_to_report = True


def loop(state, tile):
    pass
    # toggle clock

    # if falling edge
    #   increment location in word cycle
    #   if data to write
    #       toggle data pin for data
    #   else
    #       if at end of word cycle
    #           toggle data off
    #       else
    #           toggle data on
    # if rising edge
    #   read data

    # sleep until next clock edge
