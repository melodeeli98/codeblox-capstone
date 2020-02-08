import threading
import time
import random

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


class EmbeddedCode (threading.Thread):
    def __init__(self, tile):
        threading.Thread.__init__(self)
        self.tile = tile

    def run(self):
        print("booting {}".format(self.tile.syntax_name))
        time.sleep(random.uniform(0.0, 8.0))
        print("done booting {}".format(self.tile.syntax_name))


class Side:
    def __init__(self, is_sender):
        self.is_sender = is_sender
        self.data_out = 0
        self.data_in = 0

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
            self.neighbor.clk_in = value
        else:
            raise Exception("Not a sender!")

    def toggleData(self, value):
        self.data_out = value
        self.neighbor.data_in = value


class Tile:
    def __init__(self, syntax_name, is_powered=False):
        self.syntax_name = syntax_name
        self.syntax = syntax_map[syntax_name]
        self.top = Side(False)
        self.right = Side(True)
        self.bottom = Side(True)
        self.left = Side(False)
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
        # TODO
        return []

    def boot(self):
        self.is_powered = True
        thread = EmbeddedCode(self)
        thread.start()


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
                return


if __name__ == '__main__':
    main()
