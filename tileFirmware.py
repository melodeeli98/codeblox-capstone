import threading
import time
import random


class EmbeddedCode (threading.Thread):
    def __init__(self, tile):
        threading.Thread.__init__(self)
        self.tile = tile
        self.time_to_exit = False

    ### Begin Arduino functions ###

    def leftClockCallback(self):
        pass

    def topClockCallback(self):
        pass

    def init(self):
        tile = self.tile
        tile.top.registerClockCallback(self.topClockCallback)
        tile.left.registerClockCallback(self.leftClockCallback)
        self.tiles = []

    def loop(self):
        time.sleep(1)

    ### End Arduino functions ###

    def run(self):
        tile = self.tile
        print("booting {}".format(tile.syntax_name))
        tile.top.toggleData(1)
        tile.right.toggleData(1)
        tile.bottom.toggleData(1)
        tile.left.toggleData(1)
        time.sleep(random.uniform(0.0, 5.0))
        print("done booting {}".format(tile.syntax_name))
        self.init()
        while not self.time_to_exit:
            self.loop()

    def kill(self):
        self.time_to_exit = True

    def waitUntilDone(self):
        pass

    def getTiles(self):
        return self.tiles
