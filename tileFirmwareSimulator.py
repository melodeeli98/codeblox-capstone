import time
import threading
import time
import random
import firmware
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

    def waitUntilDone(self):
        while not self.ready_to_report:
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

    def disconnect(self):
        other = self.neighbor
        if (other != None):
            other.neighbor = None
            other.data_in = 0
            self.neighbor = None
            self.data_in = 0

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

    def disconnectAllSides(self):
        self.top.disconnect()
        self.left.disconnect()
        self.bottom.disconnect()
        self.right.disconnect()

    def tiles(self):
        delayMicros(10000) # Delay long enough for master tile to reset and no longer have the state of the tiles of the previous button press (if present)
        self.thread.waitUntilDone()
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

def disconnectAllTiles(tiles):
    for tile in tiles:
        tile.disconnectAllSides()

def encodingToSyntax(encoding):
    return list(syntax_map.keys())[list(syntax_map.values()).index(encoding)]

def tilesMatch(expected_tiles, actual_tiles, tiles_list):
    for i in range(len(actual_tiles)):
        for j in range(len(actual_tiles[0])):
            actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

    for r in range(len(expected_tiles)):
        for c in range(len(expected_tiles[r])):
            if r >= len(actual_tiles) or c >= len(actual_tiles[r]) or expected_tiles[r][c] != actual_tiles[r][c]:
                return False

    return True

class TestTileFirmware(unittest.TestCase):
    master_tile = Tile("none", is_master=True)
    if_tile = Tile("if")
    true_tile = Tile("true")
    output_tile_1 = Tile("output")
    else_tile = Tile("else")
    output_tile_2 = Tile("output")
    false_tile = Tile("false")
    loop_tile = Tile("loop")
    tiles_list = [master_tile, if_tile, true_tile, output_tile_1, else_tile, output_tile_2, false_tile, loop_tile]
    
    def setUp(self): # Occurs before each test
        disconnectAllTiles(self.tiles_list)

    @classmethod
    def tearDownClass(cls): # Occurs after all tests
        for tile in TestTileFirmware.tiles_list:
            tile.killThread()

    #@unittest.skip("not testing")
    def testBasic1(self):
        """
        MA
        IF
        """
        print("############## Basic Test 1 ##############")

        self.master_tile.connectBottom(self.if_tile)

        expected_tiles = [
            ["if"]
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])
                
        self.assertEqual(expected_tiles, actual_tiles)
            
    #@unittest.skip("not testing")
    def testBasic2(self):
        """
        MA
        IF TR
        """
        print("############## Basic Test 2 ##############")

        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)

        expected_tiles = [
            ["if", "true"],
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])
                
        self.assertEqual(expected_tiles, actual_tiles)
        
    #@unittest.skip("not testing")
    def testBasic3(self):
        """
        MA
        IF TR
           OU
        EL OU
        """
        print("############## Basic Test 3 ##############")
        
        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.output_tile_1.connectBottom(self.output_tile_2)
        self.output_tile_2.connectLeft(self.else_tile)

        expected_tiles = [
            ["if", "true"],
            ["none", "output"],
            ["else", "output"]
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])
                
        self.assertEqual(expected_tiles, actual_tiles)
        
    #@unittest.skip("not testing")
    def testNoSlaves(self):
        """
        MA
        """
        print("############## No Slaves Test ##############")

        expected_tiles = [[]]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        self.assertEqual(expected_tiles, actual_tiles)
        
    #@unittest.skip("not testing")
    def testPressPlayButtonTwiceQuickly(self):
        """
        MA
        IF TR
           OU
        EL OU
        """
        print("############## Play Button Twice Quickly Test ##############")

        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.output_tile_1.connectBottom(self.output_tile_2)
        self.output_tile_2.connectLeft(self.else_tile)

        expected_tiles = [
            ["if", "true"],
            ["none", "output"],
            ["else", "output"]
        ]

        self.master_tile.play()
        self.master_tile.play()
        time.sleep(1)

        for i in range(2):
            actual_tiles = self.master_tile.tiles()
            print("Checking if retrieved tiles match expected tiles")
            for i in range(len(actual_tiles)):
                for j in range(len(actual_tiles[0])):
                    actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j]) 
            self.assertEqual(expected_tiles, actual_tiles)
    
    #@unittest.skip("not testing")
    def testPressPlayButtonTwiceSlowly(self):
        """
        MA
        IF TR
        """
        print("############## Play Button Twice Slowly Test ##############")

        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.output_tile_1.connectBottom(self.output_tile_2)
        self.output_tile_2.connectLeft(self.else_tile)

        expected_tiles = [
            ["if", "true"],
            ["none", "output"],
            ["else", "output"]
        ]

        for i in range(2):
            self.master_tile.play()
            time.sleep(1)
            actual_tiles = self.master_tile.tiles()
            for i in range(len(actual_tiles)):
                for j in range(len(actual_tiles[0])):
                    actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j]) 
            self.assertEqual(expected_tiles, actual_tiles)

    #@unittest.skip("not testing")
    def testMultipleChildren(self):
        """
        MA
        IF TR FA
           OU
        """
        print("############## Multiple Children ##############")
        
        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.true_tile.connectRight(self.false_tile)

        expected_tiles = [
            ["if", "true", "false"],
            ["none", "output", "none"]
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

        print("Actual tiles: " + str(actual_tiles))
                
        self.assertEqual(expected_tiles, actual_tiles)

    #@unittest.skip("not testing")
    def testMultipleChildrenAndParents1(self):
        """
        MA
        TR FA
        OU LO
        """
        print("############## Multiple Children And Parents 1 ##############")
        
        self.master_tile.connectBottom(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.true_tile.connectRight(self.false_tile)
        self.false_tile.connectBottom(self.loop_tile)
        self.output_tile_1.connectRight(self.loop_tile)

        expected_tiles = [
            ["true", "false"],
            ["output", "loop"],
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

        print("Actual tiles: " + str(actual_tiles))
                
        self.assertEqual(expected_tiles, actual_tiles)

    #@unittest.skip("not testing")
    def testMultipleChildrenAndParents2(self):
        """
        MA
        IF TR FA
           OU LO
        EL OU
        """
        print("############## Multiple Children And Parents 2 ##############")
        
        self.master_tile.connectBottom(self.if_tile)
        self.if_tile.connectRight(self.true_tile)
        self.true_tile.connectBottom(self.output_tile_1)
        self.true_tile.connectRight(self.false_tile)
        self.false_tile.connectBottom(self.loop_tile)
        self.output_tile_1.connectRight(self.loop_tile)
        self.output_tile_1.connectBottom(self.output_tile_2)
        self.output_tile_2.connectLeft(self.else_tile)

        expected_tiles = [
            ["if", "true", "false"],
            ["none", "output", "loop"],
            ["else", "output", "none"]
        ]

        self.master_tile.play()
        time.sleep(1)
        actual_tiles = self.master_tile.tiles()
        for i in range(len(actual_tiles)):
            for j in range(len(actual_tiles[0])):
                actual_tiles[i][j] = encodingToSyntax(actual_tiles[i][j])

        print("Actual tiles: " + str(actual_tiles))
                
        self.assertEqual(expected_tiles, actual_tiles)
        
def main():
    unittest.main()

if __name__ == '__main__':
    main()
