import time
import threading
import time
import random
import slaveFirmware
import masterFirmware
from arduino import micros, delayMicros
import unittest

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

TIMEOUT = 100000000 # 100 seconds

curr_id = 0


class EmbeddedCode (threading.Thread):
    def __init__(self, tile):
        threading.Thread.__init__(self)
        self.tile = tile
        self.time_to_exit = False
        self.ready_to_report = False

    def run(self):
        self.tile.firmware.init(self, self.tile)
        while not self.time_to_exit:
            if not self.tile.asleep:
                self.tile.firmware.loop(self, self.tile)
            time.sleep(0.000000001)

    def kill(self):
        self.time_to_exit = True

    def waitUntilDone(self, timeout):
        timeoutTime = micros() + timeout
        while not self.ready_to_report:
            if (micros() > timeoutTime):
                raise Exception("Timeout while waiting for master response.")
                self.kill()
            time.sleep(0.000000001)

    def getTiles(self):
        return self.topology


class Side:
    def __init__(self, is_sender, tile):
        self.is_sender = is_sender
        self.data_out = 0
        self.data_in = 0
        self.neighbor = None
        self.tile = tile
        self.interruptHandler = lambda: None

    def connect(self, other):
        self.neighbor = other
        other.neighbor = self
        self.data_in = other.data_out
        other.data_in = self.data_out
        assert self.is_sender != other.is_sender

    def registerInterruptHandler(self, handler):
        self.interruptHandler = handler

    def toggleData(self):
        self.data_out = not self.data_out
        if self.neighbor:
            self.neighbor.data_in = self.data_out
            self.neighbor.tile.wakeUp()
            self.neighbor.interruptHandler()

    def readData(self):
        return self.data_in


class Tile:
    def __init__(self, syntax_name, is_master=False):
        global curr_id
        self.syntax_name = syntax_name
        self.id = curr_id
        curr_id += 1
        self.syntax = syntax_map[syntax_name]
        self.top = Side(False, self)
        self.right = Side(True, self)
        self.bottom = Side(True, self)
        self.left = Side(False, self)
        self.asleep = False
        self.is_master = is_master
        if (is_master):
            self.firmware = masterFirmware
        else:
            self.firmware = slaveFirmware

        self.thread = EmbeddedCode(self)
        self.thread.start()

    def log(self, s):
        if self.is_master:
            print("Master: {}".format(s))
        else:
            print(" Slave {}: {}".format(self.id, s))

    def connectTop(self, other):
        self.top.connect(other.bottom)

    def connectRight(self, other):
        self.right.connect(other.left)

    def connectBottom(self, other):
        self.bottom.connect(other.top)

    def connectLeft(self, other):
        self.left.connect(other.right)

    def tiles(self, timeout):
        self.thread.waitUntilDone(timeout)
        return self.thread.getTiles()

    def killThread(self):
        self.thread.kill()
        self.thread.join()

    def sleep(self):
        self.asleep = True

    def wakeUp(self):
        self.asleep = False

    def registerPlayHandler(self, handler):
        self.playHandler = handler

    def play(self):
        self.playHandler()

def encodingToSyntax(encoding):
    return list(syntax_map.keys())[list(syntax_map.values()).index(encoding)]

def basicTest1():
    """
    MA
    IF
    """
    print("############## Basic Test 1 ##############")

    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")

    tiles_list = [master_tile, if_tile]

    master_tile.connectBottom(if_tile)

    expected_tiles = [
        ["if"]
    ]

    master_tile.play()

    time.sleep(1)

    actual_tiles = master_tile.tiles(TIMEOUT)
    for i in range(len(actual_tiles)):
        for j in range(len(actual_tiles[0])):
            actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

    for r in range(len(expected_tiles)):
        for c in range(len(expected_tiles[r])):
            if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                print("Failure!")
                print("expected:")
                print(expected_tiles)
                print("actual: ")
                print(actual_tiles)

                for tile in tiles_list:
                    tile.killThread()
                return
    
    print("Pass!")
    for tile in tiles_list:
        tile.killThread()
    
    print()

def basicTest2():
    """
    MA
    IF TR
    """
    print("############## Basic Test 2 ##############")

    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")
    true_tile = Tile("true")

    tiles_list = [master_tile, if_tile, true_tile]

    master_tile.connectBottom(if_tile)
    if_tile.connectRight(true_tile)

    expected_tiles = [
        ["if", "true"],
    ]

    master_tile.play()

    time.sleep(1)

    actual_tiles = master_tile.tiles(TIMEOUT)
    for i in range(len(actual_tiles)):
        for j in range(len(actual_tiles[0])):
            actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

    for r in range(len(expected_tiles)):
        for c in range(len(expected_tiles[r])):
            if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                print("Failure!")
                print("expected:")
                print(expected_tiles)
                print("actual: ")
                print(actual_tiles)

                for tile in tiles_list:
                    tile.killThread()
                return
    
    print("Pass!")
    for tile in tiles_list:
        tile.killThread()

    print()

def basicTest3():
    """
    MA
    IF TR
       OU
    EL OU
    """
    print("############## Basic Test 3 ##############")

    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")
    true_tile = Tile("true")
    output_tile_1 = Tile("output")
    else_tile = Tile("else")
    output_tile_2 = Tile("output")

    tiles_list = [master_tile, if_tile, true_tile,
                  output_tile_1, else_tile, output_tile_2]

    master_tile.connectBottom(if_tile)
    if_tile.connectRight(true_tile)
    true_tile.connectBottom(output_tile_1)
    output_tile_1.connectBottom(output_tile_2)
    output_tile_2.connectLeft(else_tile)

    expected_tiles = [
        ["if", "true"],
        ["none", "output"],
        ["else", "output"]
    ]

    master_tile.play()

    time.sleep(1)

    actual_tiles = master_tile.tiles(TIMEOUT)
    for i in range(len(actual_tiles)):
        for j in range(len(actual_tiles[0])):
            actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

    for r in range(len(expected_tiles)):
        for c in range(len(expected_tiles[r])):
            if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                print("Failure!")
                print("expected:")
                print(expected_tiles)
                print("actual: ")
                print(actual_tiles)

                for tile in tiles_list:
                    tile.killThread()
                return
    
    print("Pass!")
    for tile in tiles_list:
        tile.killThread()

    print()

def noSlaveTest():
    """
    MA
    """
    print("############## No Slave Test ##############")

    master_tile = Tile("none", is_master=True)

    class Test(unittest.TestCase):
        def raisesException(self):
            self.assertRaises(Exception, master_tile.play())

    test = Test()
    
    if (test.raisesException):
        print("Pass!")
    else:
        print("Failure!")
        print("expected Exception")
    
    master_tile.killThread()
    print()

def playButtonTwiceQuicklyTest():
    """
    MA
    IF TR
       OU
    EL OU
    """
    print("############## Play Button Twice Quickly Test ##############")

    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")
    true_tile = Tile("true")
    output_tile_1 = Tile("output")
    else_tile = Tile("else")
    output_tile_2 = Tile("output")

    tiles_list = [master_tile, if_tile, true_tile,
                  output_tile_1, else_tile, output_tile_2]

    master_tile.connectBottom(if_tile)
    if_tile.connectRight(true_tile)
    true_tile.connectBottom(output_tile_1)
    output_tile_1.connectBottom(output_tile_2)
    output_tile_2.connectLeft(else_tile)

    expected_tiles = [
        ["if", "true"],
        ["none", "output"],
        ["else", "output"]
    ]

    master_tile.play()
    master_tile.play()

    time.sleep(1)

    expected_tiles = [
        ["if", "true"],
    ]

    for i in range(2):
        actual_tiles = master_tile.tiles(TIMEOUT)
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

        for r in range(len(expected_tiles)):
            for c in range(len(expected_tiles[r])):
                if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                    print("Failure!")
                    print("expected:")
                    print(expected_tiles)
                    print("actual: ")
                    print(actual_tiles)

                    for tile in tiles_list:
                        tile.killThread()
                    return
        delayMicros(1000000) # Delay long enough for master tile to reset and no longer have the state of the tiles of the previous button press
        
    print("Pass!")
    for tile in tiles_list:
        tile.killThread()

    print()

def playButtonTwiceSlowlyTest():
    """
    MA
    IF TR
    """
    print("############## Play Button Twice Slowly Test ##############")

    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")
    true_tile = Tile("true")

    tiles_list = [master_tile, if_tile, true_tile]

    master_tile.connectBottom(if_tile)
    if_tile.connectRight(true_tile)

    expected_tiles = [
        ["if", "true"],
    ]

    for i in range(2):
        master_tile.play()
        time.sleep(1)
        actual_tiles = master_tile.tiles(TIMEOUT)
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

        for r in range(len(expected_tiles)):
            for c in range(len(expected_tiles[r])):
                if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                    print("Failure!")
                    print("expected:")
                    print(expected_tiles)
                    print("actual: ")
                    print(actual_tiles)

                    for tile in tiles_list:
                        tile.killThread()
                    return
        #delayMicros(2000000)
        
    print("Pass!")
    for tile in tiles_list:
        tile.killThread()

    print()

def main():
    #basicTest1()
    #basicTest2()
    #basicTest3()
    #noSlaveTest()
    #playButtonTwiceQuicklyTest()
    #playButtonTwiceSlowlyTest()


if __name__ == '__main__':
    main()
