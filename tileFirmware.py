import time


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
    time.sleep(1)
