import time
from tileFirmware import EmbeddedCode

NONE = 0
IF = 1
ELSE = 2
LOOP = 3
TRUE = 4
FALSE = 5
INPUT = 6
OUTPUT = 7

syntax_map = {
    "none": 0,
    "if": 1,
    "else": 2,
    "loop": 3,
    "true": 4,
    "false": 5,
    "input": 6,
    "output": 7
}


class Side:
    def __init__(self, is_sender, tile):
        self.is_sender = is_sender
        self.data_out = 0
        self.data_in = 0
        self.clockCallback = lambda: None
        self.neighbor = None
        self.tile = tile

        if is_sender:
            self.clk_out = 0
        else:
            self.clk_in = 0

    def connect(self, other):
        self.neighbor = other
        other.neighbor = self
        self.data_in = other.data_out
        other.data_in = self.data_out
        assert self.is_sender != other.is_sender
        if self.is_sender:
            other.clk_in = self.clk_out

    def toggleClock(self, value):
        if self.is_sender:
            self.clk_out = value
            if self.neighbor:
                self.neighbor.clk_in = value
                self.neighbor.clockCallback()
        else:
            raise Exception("Not a sender!")

    def registerClockCallback(self, callback):
        self.clockCallback = callback

    def toggleData(self, value):
        self.data_out = value
        if self.neighbor:
            self.neighbor.data_in = value


class Tile:
    def __init__(self, syntax_name, is_powered=False):
        self.syntax_name = syntax_name
        self.syntax = syntax_map[syntax_name]
        self.top = Side(False, self)
        self.right = Side(True, self)
        self.bottom = Side(True, self)
        self.left = Side(False, self)
        self.is_powered = is_powered
        if is_powered:
            self.boot()

    def connectTop(self, other):
        self.top.connect(other.bottom)
        if not self.is_powered and other.is_powered:
            self.boot()
        if self.is_powered and not other.is_powered:
            other.boot()

    def connectRight(self, other):
        self.right.connect(other.left)
        if not self.is_powered and other.is_powered:
            self.boot()
        if self.is_powered and not other.is_powered:
            other.boot()

    def connectBottom(self, other):
        self.bottom.connect(other.top)
        if not self.is_powered and other.is_powered:
            self.boot()
        if self.is_powered and not other.is_powered:
            other.boot()

    def connectLeft(self, other):
        self.left.connect(other.right)
        if not self.is_powered and other.is_powered:
            self.boot()
        if self.is_powered and not other.is_powered:
            other.boot()

    def tiles(self):
        self.thread.waitUntilDone()
        return self.thread.getTiles()

    def killThread(self):
        self.thread.kill()
        self.thread.join()

    def boot(self):
        self.is_powered = True
        sides = [self.top, self.right, self.bottom, self.left]
        for side in sides:
            if side.neighbor:
                if not side.neighbor.tile.is_powered:
                    side.neighbor.tile.boot()

        self.thread = EmbeddedCode(self)
        self.thread.start()

"""
IF TR
   OU
EL OU
"""

def main():
    if_tile = Tile("if", is_powered=True)
    true_tile = Tile("true")
    output_tile_1 = Tile("output")
    else_tile = Tile("else")
    output_tile_2 = Tile("output")

    tiles_list = [if_tile, true_tile, output_tile_1, else_tile, output_tile_2]

    if_tile.connectRight(true_tile)
    true_tile.connectBottom(output_tile_1)
    output_tile_1.connectBottom(output_tile_2)
    output_tile_2.connectLeft(else_tile)

    time.sleep(10)

    expected_tiles = [
        ["if", "true"],
        ["none", "output"],
        ["else", "output"]
    ]
    actual_tiles = if_tile.tiles()

    for r in range(len(expected_tiles)):
        for c in range(len(expected_tiles[r])):
            if r >= len(actual_tiles) or c >= len(expected_tiles) or expected_tiles[r][c] != actual_tiles[r][c]:
                print("Failure!")
                print("expected:")
                print(expected_tiles)
                print("actual: ")
                print(actual_tiles)

                for tile in tiles_list:
                    tile.killThread()
                
                return


if __name__ == '__main__':
    main()
