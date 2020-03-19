import time
from arduino import micros, delayMicros
import firmware
from firmware import SideStateMachine, TileStateMachine, TIMEOUT, CLOCK_PERIOD, Message
import util

def topInterruptHandler(state, tile):
    time_received = micros()
    if (state.sides["top"].neighborIsValid and tile.top.readData()): # Data is high
        #tile.log("received top pulse at {}!".format(time_received))
        if (state.sides["top"].neighborLastHighTime == -1):
           if (state.sides["bottom"].neighborLastHighTime == -1 and state.sides["right"].neighborLastHighTime == -1 and state.sides["left"].neighborLastHighTime == -1):
                # Top sending wake up signal
                tile.log("woke up")
                state.sides["top"].neighborLastHighTime = time_received
                # Send wakeup messages to other sides
                state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["top"].handlePulseReceived(time_received, " Slave 1")

def leftInterruptHandler(state, tile):
    time_received = micros()
    if (state.sides["left"].neighborIsValid and tile.left.readData()): # Data is high
        tile.log("received left pulse at {}!".format(time_received))
        if (state.sides["left"].neighborLastHighTime == -1):
            if (state.sides["top"].neighborLastHighTime == -1 and state.sides["right"].neighborLastHighTime == -1 and state.sides["bottom"].neighborLastHighTime == -1):
                # Left sending wake up signal
                state.sides["left"].neighborLastHighTime = time_received
                # Send wakeup messages to other sides
                state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["left"].handlePulseReceived(time_received, "    Slave 1")

def rightInterruptHandler(state, tile):
    time_received = micros()
    if (state.sides["right"].neighborIsValid and tile.right.readData()): # Data is high
        tile.log("received right pulse at {}!".format(time_received))
        if (state.sides["right"].neighborLastHighTime == -1):
            if (state.sides["top"].neighborLastHighTime == -1 and state.sides["bottom"].neighborLastHighTime == -1 and state.sides["left"].neighborLastHighTime == -1):
                # Right sending wake up signal
                state.sides["right"].neighborLastHighTime = time_received
                # Send wakeup messages to other sides
                state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["right"].handlePulseReceived(time_received, "   Slave 1")

def bottomInterruptHandler(state, tile):
    time_received = micros()
    if (state.sides["bottom"].neighborIsValid and tile.bottom.readData()): # Data is high
        tile.log("received bottom pulse at {}!".format(time_received))
        if (state.sides["bottom"].neighborLastHighTime == -1):
            if (state.sides["top"].neighborLastHighTime == -1 and state.sides["right"].neighborLastHighTime == -1 and state.sides["left"].neighborLastHighTime == -1):
                # Bottom sending wake up signal
                state.sides["bottom"].neighborLastHighTime = time_received
                # Send wakeup messages to other sides
                state.sides["top"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["left"].enqueueMessage(Message(False, firmware.WAKE_UP))
                state.sides["right"].enqueueMessage(Message(False, firmware.WAKE_UP))
        else:
            state.sides["bottom"].handlePulseReceived(time_received, "  Slave 1")

def resetTile(state, tile):
    tile.log("resetting tile")
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

    state.topology = [[tile.syntax]]
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
    if (length_difference > 0):
        length_difference -= 1
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
                if ([message] == firmware.AWAKE_MESSAGE):
                    tile.log("awake")
                    return

                numTiles = util.binaryListToUnsignedInt(message[1:-2])
                tile.log("numTiles:" + str(numTiles))
                state.sides[sideName].numTileInfoExpected = numTiles
                state.sides[sideName].neighborTopology = [[-1 for i in range(numTiles * 2 + 1)] for j in range(numTiles * 2 + 1)]
                midpoint = len(state.sides[sideName].neighborTopology) // 2
                state.sides[sideName].neighborTopology[midpoint][midpoint] = tile.syntax_name
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_X_COORDINATE):
                xCoordinate = util.binaryListToSignedInt(message[1:-2])
                tile.log("xCoordinate:" + str(xCoordinate))
                state.sides[sideName].currXCoordinate = xCoordinate
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_Y_COORDINATE
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_Y_COORDINATE):
                yCoordinate = util.binaryListToSignedInt(message[1:-2])
                tile.log("yCoordinate:" + str(yCoordinate))
                state.sides[sideName].currYCoordinate = yCoordinate
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_ENCODING
                return
            elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_ENCODING):
                encoding = util.binaryListToUnsignedInt(message[1:-2])
                tile.log("encoding:" + str(encoding))
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
                    return
                else:
                    state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
                    state.topology = combineTopologies(state.sides[sideName].neighborTopology, state.topology)
                    return

        elif ([message] == firmware.REQUEST_PARENT_TOP):
            tile.log("request parent top")
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.YES_MESSAGE))
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
            return

        elif ([message] == firmware.REQUEST_PARENT_LEFT):
            tile.log("request parent left")
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.YES_MESSAGE))
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
            return  

        elif ([message] == firmware.REQUEST_PARENT_BOTTOM):
            tile.log("request parent bottom")
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.YES_MESSAGE))
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
            return

        elif ([message] == firmware.REQUEST_PARENT_RIGHT):
            tile.log("request parent right")
            if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, firmware.YES_MESSAGE))
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
            return

        elif ([message] == firmware.YES_MESSAGE):
            tile.log("yes")
            if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
                state.sides[sideName].neighborIsValid = False
                return
            state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_NUM_TILES
            return

        elif ([message] == firmware.NO_MESSAGE):
            tile.log("no")
            if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
                state.sides[sideName].neighborIsValid = False
                return

        elif ([message] == firmware.AWAKE_MESSAGE):
            tile.log("awake")
            return

        else:
            tile.log("invalid message")
            state.sides[sideName].neighborIsValid = False
            return

def loop(state, tile):
    curr_time = micros()
    #next_check_timeout_time = micros() + TIMEOUT
    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid):
            if (micros() - sideState.neighborLastHighTime > TIMEOUT):
                # Neighbor died
                tile.log(sideName + " side timed out")
                # sideState.reset() # TODO is this necessary?
                sideState.neighborIsValid = False
                if (state.tile_state.parentName == sideName):
                    # Parent died, therefore this tile should reset
                    resetTile(state, tile)
                    tile.sleep()
                    tile.killThread()
            #else:
                #if (sideState.neighborLastHighTime + TIMEOUT < next_check_timeout_time):
                    #next_check_timeout_time = sideState.neighborLastHighTime + TIMEOUT

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
        #tile.log(state.sides["top"].messagesToSend)
        #tile.log("Sending " + str(bit))
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

    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid and sideState.sideState != firmware.SideState.NOT_CHILD and sideState.sideState != firmware.SideState.FINISHED_SENDING_TOPOLOGY):
            # Not ready to forward topology to parent.
            delayMicros(CLOCK_PERIOD - (micros() - curr_time))
            return
    
    if (state.tile_state.parentName != None and not state.tile_state.reportedTopology):
        # All neighbors are either not valid, not child, or done sending topology. Ready to forward topology to parent.
        state.ready_to_report = True
        state.tile_state.reportedTopology = True
        tile.log("Sending topology to parent")
        state.sides[state.tile_state.parentName].enqueueTopology(state.topology)
    
    #curr_time = micros()
    #if (next_check_timeout_time - curr_time > 0):
        #delayMicros(next_check_timeout_time - curr_time)
    delayMicros(CLOCK_PERIOD - (micros() - curr_time))