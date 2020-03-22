import time
from arduino import micros, delayMicros
import firmware
from firmware import SideStateMachine, TileStateMachine, TIMEOUT, CLOCK_PERIOD, Message
import util

def firstPulseReceived(state):
    return state.sides["top"].neighborLastHighTime == -1 and state.sides["bottom"].neighborLastHighTime == -1 and state.sides["right"].neighborLastHighTime == -1 and state.sides["left"].neighborLastHighTime == -1

def wakeUpOtherSides(tile, state, sideName):
    for (name, sideState) in state.sides.items():
        if (sideName != name):
            state.sides[name].enqueueMessage(Message(False, firmware.WAKE_UP), "  Slave " + str(tile.id))

def sideInterruptHandler(state, tile, dataHigh, sideName):
    time_received = micros()
    if (state.sides[sideName].neighborIsValid and dataHigh):
        #tile.log("received " + sideName + " pulse at {}!".format(time_received))
        if (firstPulseReceived(state)):
            # Side sent wake up signal
            tile.log("woke up")
            wakeUpOtherSides(tile, state, sideName)
        else:
            state.sides[sideName].handlePulseReceived(time_received, " Slave " + str(tile.id) + " " + sideName)
        state.sides[sideName].neighborLastHighTime = time_received

def resetTile(state, tile):
    tile.log("resetting tile")
    state.tile_state.reset()
    init(state, tile)

def init(state, tile):
    tile.log("initializing")
    tile.top.registerInterruptHandler(lambda: sideInterruptHandler(state, tile, tile.top.readData(), "top"))
    tile.left.registerInterruptHandler(lambda: sideInterruptHandler(state, tile, tile.left.readData(), "left"))
    tile.right.registerInterruptHandler(lambda: sideInterruptHandler(state, tile, tile.right.readData(), "right"))
    tile.bottom.registerInterruptHandler(lambda: sideInterruptHandler(state, tile, tile.bottom.readData(), "bottom"))

    state.topology = [[tile.syntax]]
    state.ready_to_report = False

    state.tile_state = TileStateMachine()
    state.sides = {"top": SideStateMachine(), "left": SideStateMachine(), "right": SideStateMachine(), "bottom": SideStateMachine()}

    tile.sleep()

def combineTopologies(tile, top1, top2):
    result = top1 if (len(top1) > len(top2)) else top2
    shorter_top = top1 if (len(top1) <= len(top2)) else top2
    length_difference = abs(len(top1) - len(top2))
    if (length_difference > 0):
        length_difference -= 1
    for i in range(len(shorter_top)):
        for j in range(len(shorter_top[0])):
            if (shorter_top[i][j] != 0):
                if (result[i + length_difference][j + length_difference] != shorter_top[i][j]):
                    if (result[i + length_difference][j + length_difference] != 0):
                        raise Exception("Conflicting child topologies.")
                    result[i + length_difference][j +
                                                length_difference] = shorter_top[i][j]
    tile.log("topology is now " + str(result))
    return result

def rotateSidesCCW(state):
    oldLeft = state.sides["left"]
    state.sides["left"] = state.sides["top"]
    state.sides["top"] = state.sides["right"]
    state.sides["right"] = state.sides["bottom"]
    state.sides["bottom"] = oldLeft

def adjustSideNames(state, sideName, parentSideName):
    names = ["top", "left", "bottom", "right"]
    numCCWRotations = abs(names.index(sideName) - names.index(parentSideName))
    for i in range(numCCWRotations):
        rotateSidesCCW(state)

def processRequestParentMessage(state, tile, sideName, parentSideName):
    tile.log(sideName + " received request parent " + parentSideName)
    if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
        # Tile already has a parent
        state.sides[sideName].enqueueMessage(Message(True, firmware.NO_MESSAGE), "  Slave " + str(tile.id))
        return
    # Say yes to parent
    state.sides[sideName].enqueueMessage(Message(True, firmware.YES_MESSAGE), "  Slave " + str(tile.id))
    # Adjust side names if necessary
    adjustSideNames(state, sideName, parentSideName)
    state.tile_state.parentName = parentSideName
    # Send parent request to neighbors
    state.sides[parentSideName].sideState = firmware.SideState.NOT_CHILD
    state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
    for (name, sideState) in state.sides.items():
        if (name != parentSideName):
            if name == "top":
                requestParentMessage = firmware.REQUEST_PARENT_BOTTOM
            elif name == "right":
                requestParentMessage = firmware.REQUEST_PARENT_LEFT
            elif name == "bottom":
                requestParentMessage = firmware.REQUEST_PARENT_TOP
            else: # left
                requestParentMessage = firmware.REQUEST_PARENT_RIGHT
            state.sides[name].enqueueMessage(Message(True, requestParentMessage), "  Slave " + str(tile.id))

def processMessage(state, tile, sideName, message):
    if (state.tile_state.tileState == firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES):
        if (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
            if ([message] == firmware.AWAKE_MESSAGE):
                tile.log(sideName + " received awake message")
                return

            numTiles = util.binaryListToUnsignedInt(message[1:-2])
            tile.log(sideName + " received numTiles: " + str(numTiles))
            state.sides[sideName].numTileInfoExpected = numTiles
            state.sides[sideName].neighborTopology = [[0 for i in range(numTiles * 2 + 1)] for j in range(numTiles * 2 + 1)]
            midpoint = len(state.sides[sideName].neighborTopology) // 2
            state.sides[sideName].neighborTopology[midpoint][midpoint] = tile.syntax
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
            return
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_X_COORDINATE):
            xCoordinate = util.binaryListToSignedInt(message[1:-2])
            tile.log(sideName + " received xCoordinate: " + str(xCoordinate))
            state.sides[sideName].currXCoordinate = xCoordinate
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_Y_COORDINATE
            return
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_Y_COORDINATE):
            yCoordinate = util.binaryListToSignedInt(message[1:-2])
            tile.log(sideName + " received yCoordinate: " + str(yCoordinate))
            state.sides[sideName].currYCoordinate = yCoordinate
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_ENCODING
            return
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_ENCODING):
            encoding = util.binaryListToUnsignedInt(message[1:-2])
            tile.log(sideName + " received encoding:" + str(encoding))
            midpoint = len(state.sides[sideName].neighborTopology) // 2
            xOffset = 0
            yOffset = 0
            if (sideName == "bottom"):
                yOffset = 1
            elif (sideName == "top"):
                yOffset = -1
            elif (sideName == "left"):
                xOffset = -1
            else: # Right
                xOffset = 1
            state.sides[sideName].neighborTopology[midpoint + state.sides[sideName].currYCoordinate + yOffset][midpoint + state.sides[sideName].currXCoordinate + xOffset] = encoding
            state.sides[sideName].numTileInfoExpected -= 1
            if (state.sides[sideName].numTileInfoExpected > 0):
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
                return
            else:
                state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
                state.topology = combineTopologies(tile, state.sides[sideName].neighborTopology, state.topology)
                return

    elif ([message] == firmware.REQUEST_PARENT_TOP):
        processRequestParentMessage(state, tile, sideName, "top")
        return

    elif ([message] == firmware.REQUEST_PARENT_LEFT):
        processRequestParentMessage(state, tile, sideName, "left")
        return

    elif ([message] == firmware.REQUEST_PARENT_BOTTOM):
        processRequestParentMessage(state, tile, sideName, "bottom")
        return

    elif ([message] == firmware.REQUEST_PARENT_RIGHT):
        processRequestParentMessage(state, tile, sideName, "right")
        return

    elif ([message] == firmware.YES_MESSAGE):
        tile.log(sideName + " received yes")
        if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
            state.sides[sideName].neighborIsValid = False
            return
        state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
        state.sides[sideName].sideState = firmware.SideState.EXPECTING_NUM_TILES
        return

    elif ([message] == firmware.NO_MESSAGE):
        tile.log(sideName + " received no")
        if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tile_state.parentName == sideName):
            state.sides[sideName].neighborIsValid = False
            return

    elif ([message] == firmware.AWAKE_MESSAGE):
        tile.log(sideName + " received awake")
        return

    else:
        tile.log(sideName + " received invalid message")
        state.sides[sideName].neighborIsValid = False
        return

def loop(state, tile):
    curr_time = micros()
    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid):
            now = micros()
            if (now - sideState.neighborLastHighTime > TIMEOUT):
                # Neighbor died
                tile.log(sideName + " timed out. last high time: " + str(sideState.neighborLastHighTime) + " current time: " + str(now))
                # sideState.reset() # TODO is this necessary?
                sideState.neighborIsValid = False
                if (state.tile_state.parentName == sideName):
                    # Parent died, therefore this tile should reset
                    resetTile(state, tile)
                    tile.sleep()
                    tile.killThread()

    # Read messages
    if (state.sides["top"].hasMessage() and state.sides["top"].neighborIsValid):
        processMessage(state, tile, "top", state.sides["top"].getNextMessage())
    elif (state.sides["right"].hasMessage() and state.sides["right"].neighborIsValid):
        processMessage(state, tile, "right", state.sides["right"].getNextMessage())
    elif (state.sides["left"].hasMessage() and state.sides["left"].neighborIsValid):
        processMessage(state, tile, "left", state.sides["left"].getNextMessage())
    elif (state.sides["bottom"].hasMessage() and state.sides["bottom"].neighborIsValid):
        processMessage(state, tile, "bottom", state.sides["bottom"].getNextMessage())

    # Write bits to sides
    if (state.sides["top"].neighborIsValid):
        bit = state.sides["top"].getNextBitToSend()
        #if (tile.id == 1):
            #tile.log("Top messages to send: " + str(state.sides["top"].messagesToSend))
            #tile.log("Top sending bit: " + str(bit))
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
    
    delayMicros(CLOCK_PERIOD - (micros() - curr_time))