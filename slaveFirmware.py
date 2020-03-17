import time
from arduino import micros, delayMicros
import firmware
from firmware import SideStateMachine, TileStateMachine, TIMEOUT, CLOCK_PERIOD, Message
import util

def topInterruptHandler(state, tile):
    if (state.sides["top"].neighborIsValid and tile.top.readData()): # Data is high
        time_received = micros()
        tile.log("received top pulse at {}!".format(time_received))
        if (state.sides["top"].neighborLastHighTime == -1):
            # Top is now alive
            state.sides["top"].neighborLastHighTime = time_received
            # Send wakeup messages to other sides
            state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["top"].handlePulseReceived(time_received)

def leftInterruptHandler(state, tile):
    if (state.sides["left"].neighborIsValid and tile.left.readData()): # Data is high
        time_received = micros()
        tile.log("received left pulse at {}!".format(time_received))
        if (state.sides["left"].neighborLastHighTime == -1):
            # Left is now alive
            state.sides["left"].neighborLastHighTime = time_received
            # Send wakeup messages to other sides
            state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["left"].handlePulseReceived(time_received)

def rightInterruptHandler(state, tile):
    if (state.sides["right"].neighborIsValid and tile.right.readData()): # Data is high
        time_received = micros()
        tile.log("received right pulse at {}!".format(time_received))
        if (state.sides["right"].neighborLastHighTime == -1):
            # Right is now alive
            state.sides["right"].neighborLastHighTime = time_received
            # Send wakeup messages to other sides
            state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["right"].handlePulseReceived(time_received)

def bottomInterruptHandler(state, tile):
    if (state.sides["bottom"].neighborIsValid and tile.bottom.readData()): # Data is high
        time_received = micros()
        tile.log("received bottom pulse at {}!".format(time_received))
        if (state.sides["bottom"].neighborLastHighTime == -1):
            # Bottom is now alive
            state.sides["bottom"].neighborLastHighTime = time_received
            # Send wakeup messages to other sides
            state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
            state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["bottom"].handlePulseReceived(time_received)

def resetTile(state, tile):
    state.tile_state.reset()
    init(state, tile)

def init(state, tile):
    tile.log("initializing")
    tile.top.registerInterruptHandler(lambda: topInterruptHandler(state, tile))
    tile.left.registerInterruptHandler(
        lambda: leftInterruptHandler(state, tile))
    tile.right.registerInterruptHandler(
        lambda: rightInterruptHandler(state, tile))
    tile.bottom.registerInterruptHandler(
        lambda: bottomInterruptHandler(state, tile))

    state.topology = []
    state.ready_to_report = False

    state.tile_state = TileStateMachine()
    state.sides = {"top": SideStateMachine(), "left": SideStateMachine(), "right": SideStateMachine(), "bottom": SideStateMachine()}

    tile.sleep()

def rotateSidesCCW(state):
    oldLeft = state.sides["left"]
    state.sides["left"] = state.sides["top"]
    state.sides["top"] = state.sides["right"]
    state.sides["right"] = state.sides["bottom"]
    state.sides["bottom"] = oldLeft

def combineTopologies(top1, top2):
    result = top1 if (len(top1) > len(top2)) else top2
    shorter_top = top1 if (len(top1) <= len(top2)) else top2
    length_difference = abs(len(top1) - len(top2))
    for i in range(len(shorter_top)):
        for j in range(len(shorter_top[0])):
            if (shorter_top[i][j] != 0):
                if (result[i + length_difference][j + length_difference] != 0):
                    raise Exception("Conflicting child topologies.")
                result[i + length_difference][j +
                                            length_difference] = shorter_top[i][j]
    return result

def processMessage(state, tile, sideName):
    if (state.sides[sideName].neighborIsValid):
        message = state.sides[sideName].getNextMessage()

        if (state.tile_state.tileState == firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES):
            if (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
                numTiles = util.binaryListToUnsignedInt(message)
                state.sides[sideName].numTileInfoExpected = numTiles
                state.sides[sideName].neighborTopology = [[-1 for i in range(numTiles * 2 + 1)] for j in range(numTiles * 2 + 1)]
                midpoint = len(state.sides[sideName].neighborTopology) // 2
                state.sides[sideName].neighborTopology[midpoint][midpoint] = tile.syntax_name
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_X_COORDINATE):
                xCoordinate = util.binaryListToSignedInt(message)
                state.sides[sideName].currXCoordinate = xCoordinate
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_Y_COORDINATE
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_Y_COORDINATE):
                yCoordinate = util.binaryListToSignedInt(message)
                state.sides[sideName].currYCoordinate = yCoordinate
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_ENCODING
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_ENCODING):
                encoding = util.binaryListToUnsignedInt(message)
                midpoint = len(state.sides[sideName].neighborTopology) // 2
                xOffset = 0
                yOffset = 0
                if (sideName == "bottom"):
                    xOffset = 1
                elif (sideName == "top"):
                    xOffset = -1
                elif (sideName == "left"):
                    yOffset = -1
                else: # Right
                    yOffset = 1
                state.sides[sideName].neighborTopology[midpoint + state.sides[sideName].currYCoordinate + xOffset][midpoint + state.sides[sideName].currXCoordinate + yOffset] = encoding
                state.sides[sideName].numTileInfoExpected -= 1
                if (state.sides[sideName].numTileInfoExpected > 0):
                    state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
                else:
                    state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
                    state.topology = combineTopologies(state.sides[sideName].neighborTopology, state.topology)
                    for (sideName, sideState) in state.sides.items():
                        if (sideState.neighborIsValid and sideState.sideState != firmware.SideState.NOT_CHILD and sideState.sideState != firmware.SideState.FINISHED_SENDING_TOPOLOGY):
                            # Not ready to forward topology to parent.
                            return
                    # All neighbors are either not valid, not child, or done sending topology. Ready to forward topology to parent.
                    state.ready_to_report = True
                    state.sides[state.tile_state.parentName].enqueueTopology(state.topology)
                    return

        elif (message == firmware.REQUEST_PARENT_TOP):
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
            # Adjust side names if necessary
            if (sideName == "left"):
                rotateSidesCCW(state)
            elif (sideName == "bottom"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            elif (sideName == "right"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            state.tile_state.parentName = "top"
            # Send parent request to neighbors
            state.sides["top"].sideState = firmware.SideState.NOT_CHILD
            state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_TOP))
            state.sides["right"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_LEFT))
            state.sides["left"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_RIGHT))

        elif (message == firmware.REQUEST_PARENT_LEFT):
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
            # Adjust side names if necessary
            if (sideName == "bottom"):
                rotateSidesCCW(state)
            elif (sideName == "right"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            elif (sideName == "top"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            state.tile_state.parentName = "left"
            # Send parent request to neighbors
            state.sides["left"].sideState = firmware.SideState.NOT_CHILD
            state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_TOP))
            state.sides["right"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_LEFT))
            state.sides["top"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_BOTTOM))    

        elif (message == firmware.REQUEST_PARENT_BOTTOM):
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
            # Adjust side names if necessary
            if (sideName == "right"):
                rotateSidesCCW(state)
            elif (sideName == "top"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            elif (sideName == "left"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            state.tile_state.parentName = "bottom"
            # Send parent request to neighbors
            state.sides["bottom"].sideState = firmware.SideState.NOT_CHILD
            state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["left"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_RIGHT))
            state.sides["right"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_LEFT))
            state.sides["top"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_BOTTOM))  

        elif (message == firmware.REQUEST_PARENT_RIGHT):
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
            # Adjust side names if necessary
            if (sideName == "right"):
                rotateSidesCCW(state)
            elif (sideName == "top"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            elif (sideName == "left"):
                rotateSidesCCW(state)
                rotateSidesCCW(state)
                rotateSidesCCW(state)
            state.tile_state.parentName = "right"
            # Send parent request to neighbors
            state.sides["right"].sideState = firmware.SideState.NOT_CHILD
            state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_TOP))
            state.sides["left"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_RIGHT))
            state.sides["top"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_BOTTOM))

        elif (message == firmware.YES_MESSAGE):
            if (state.tile_state != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
                state.sides[sideName].neighborIsValid = False
                return
            state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
            state.sides[sideName] = firmware.SideState.EXPECTING_NUM_TILES

        elif (message == firmware.NO_MESSAGE):
            if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
                state.sides[sideName].neighborIsValid = False
                return

        elif (message == firmware.AWAKE_MESSAGE):
            return

        else:
            state.sides[sideName].neighborIsValid = False

def loop(state, tile):
    next_check_timeout_time = micros() + TIMEOUT
    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid):
            if (micros() - sideState.neighborLastHighTime > TIMEOUT):
                # Neighbor died
                sideState.neighborIsValid = False
                sideState.reset()
                if (state.tile_state.parentName == sideName):
                    # Parent died, therefore this tile should reset
                    resetTile(state, tile)
                    tile.sleep()
            else:
                if (sideState.neighborLastHighTime + TIMEOUT < next_check_timeout_time):
                    next_check_timeout_time = sideState.neighborLastHighTime + TIMEOUT

    # Read messages
    if (state.sides["top"].hasMessage()):
        processMessage(state, tile, "top")
    elif (state.sides["right"].hasMessage()):
        processMessage(state, tile, "right")
    elif (state.sides["left"].hasMessage()):
        processMessage(state, tile, "left")
    elif (state.sides["bottom"].hasMessage()):
        processMessage(state, tile, "bottom")

    # Write bits to sides
    if (state.sides["top"].neighborIsValid):
        bit = state.sides["top"].getNextBitToSend()
        if bit > 0:
            firmware.sendPulse(tile.top)
    if (state.sides["bottom"].neighborIsValid):
        bit = state.sides["bottom"].getNextBitToSend()
        if bit > 0:
            firmware.sendPulse(tile.bottom)
    if (state.sides["left"].neighborIsValid):
        bit = state.sides["left"].getNextBitToSend()
        if bit > 0:
            firmware.sendPulse(tile.left)
    if (state.sides["right"].neighborIsValid):
        bit = state.sides["right"].getNextBitToSend()
        if bit > 0:
            firmware.sendPulse(tile.right)
    
    curr_time = micros()
    if (next_check_timeout_time - curr_time > 0):
        delayMicros(next_check_timeout_time - curr_time)
