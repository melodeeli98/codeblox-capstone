import time
import firmware
from firmware import SideStateMachine, TileStateMachine, TIMEOUT, CLOCK_PERIOD, Message
from arduino import micros, delayMicros
import util


def wakeUpOtherSides(tile, state):
    for (name, sideState) in state.sides.items():
        if (not state.sides[name].sentWakeUp):
            state.sides[name].enqueueMessage(Message(firmware.WAKE_UP))
            state.sides[name].sentWakeUp = True


def sideInterruptHandler(state, tile, dataHigh, sideName):
    time_received = micros()
    if (state.sides[sideName].neighborIsValid and dataHigh):
        state.sides[sideName].sideMutex.acquire()
        #tile.log("received " + sideName + " pulse at {}!".format(time_received))
        if (not state.sides[sideName].receivedWakeUp):
            # Side sent wake up signal
            wakeUpOtherSides(tile, state)
            state.sides[sideName].receivedWakeUp = True
            if (state.tile_state.wakeupTime) == -1:
                #tile.log("woke up")
                state.tile_state.wakeupTime = time_received
        else:
            state.sides[sideName].newPulseTimes.append(time_received)
            state.sides[sideName].newPulseTimes.sort()
        state.sides[sideName].neighborLastHighTime = time_received
        state.sides[sideName].sideMutex.release()


def resetTile(state, tile):
    tile.log("Resetting tile")
    init(state, tile)


def init(state, tile):
    tile.log("Initializing tile")
    tile.top.registerInterruptHandler(lambda: sideInterruptHandler(
        state, tile, tile.top.readData(), "top"))
    tile.left.registerInterruptHandler(lambda: sideInterruptHandler(
        state, tile, tile.left.readData(), "left"))
    tile.right.registerInterruptHandler(lambda: sideInterruptHandler(
        state, tile, tile.right.readData(), "right"))
    tile.bottom.registerInterruptHandler(lambda: sideInterruptHandler(
        state, tile, tile.bottom.readData(), "bottom"))

    state.topology = [[tile.syntax]]
    state.ready_to_report = False

    state.tile_state = TileStateMachine()
    state.sides = {"top": SideStateMachine(), "left": SideStateMachine(
    ), "right": SideStateMachine(), "bottom": SideStateMachine()}

    tile.sleep()


def combineTopologies(tile, top1, top2):
    result = top1 if (len(top1) > len(top2)) else top2
    shorter_top = top1 if (len(top1) <= len(top2)) else top2
    midpointDifference = (len(result) // 2) - (len(shorter_top) // 2)
    for i in range(len(shorter_top)):
        for j in range(len(shorter_top[0])):
            if (shorter_top[i][j] != 0):
                if (result[i + midpointDifference][j + midpointDifference] != shorter_top[i][j]):
                    if (result[i + midpointDifference][j + midpointDifference] != 0):
                        raise Exception("Conflicting child topologies.")
                    result[i + midpointDifference][j +
                                                   midpointDifference] = shorter_top[i][j]
    #tile.log("Topology is now " + str(result))
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
    #tile.log(sideName + " received request parent " + parentSideName)
    if (state.tile_state.tileState != firmware.TileState.WAITING_FOR_PARENT_REQUEST):
        # Tile already has a parent
        state.sides[sideName].enqueueMessage(Message(firmware.NO_MESSAGE))
        return
    # Say yes to parent
    state.sides[sideName].enqueueMessage(Message(firmware.YES_MESSAGE))
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
            else:  # left
                requestParentMessage = firmware.REQUEST_PARENT_RIGHT
            state.sides[name].enqueueMessage(Message(requestParentMessage))


def processMessage(state, tile, sideName, message):
    if (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
        if ([message] == firmware.AWAKE_MESSAGE):
            #tile.log(sideName + " received awake message")
            return

        numTiles = util.binaryListToUnsignedInt(message[1:-2])
        #tile.log(sideName + " received numTiles: " + str(numTiles))
        state.sides[sideName].numTileInfoExpected = numTiles
        state.sides[sideName].neighborTopology = [
            [0 for i in range(numTiles * 2 + 1)] for j in range(numTiles * 2 + 1)]
        midpoint = len(state.sides[sideName].neighborTopology) // 2
        state.sides[sideName].neighborTopology[midpoint][midpoint] = tile.syntax
        state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
        return
    elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_X_COORDINATE):
        xCoordinate = util.binaryListToSignedInt(message[1:-2])
        #tile.log(sideName + " received xCoordinate: " + str(xCoordinate))
        state.sides[sideName].currXCoordinate = xCoordinate
        state.sides[sideName].sideState = firmware.SideState.EXPECTING_Y_COORDINATE
        return
    elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_Y_COORDINATE):
        yCoordinate = util.binaryListToSignedInt(message[1:-2])
        #tile.log(sideName + " received yCoordinate: " + str(yCoordinate))
        state.sides[sideName].currYCoordinate = yCoordinate
        state.sides[sideName].sideState = firmware.SideState.EXPECTING_ENCODING
        return
    elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_ENCODING):
        encoding = util.binaryListToUnsignedInt(message[1:-2])
        #tile.log(sideName + " received encoding: " + str(encoding))
        midpoint = len(state.sides[sideName].neighborTopology) // 2
        xOffset = 0
        yOffset = 0
        if (sideName == "bottom"):
            yOffset = 1
        elif (sideName == "top"):
            yOffset = -1
        elif (sideName == "left"):
            xOffset = -1
        else:  # Right
            xOffset = 1
        state.sides[sideName].neighborTopology[midpoint + state.sides[sideName].currYCoordinate +
                                               yOffset][midpoint + state.sides[sideName].currXCoordinate + xOffset] = encoding
        state.sides[sideName].numTileInfoExpected -= 1
        if (state.sides[sideName].numTileInfoExpected > 0):
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
            return
        else:
            state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
            #tile.log(sideName + " is no longer valid")
            state.sides[sideName].neighborIsValid = False
            state.topology = combineTopologies(
                tile, state.sides[sideName].neighborTopology, state.topology)
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
        if ((state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS and state.tile_state.tileState != firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES) or state.tile_state.parentName == sideName):
            tile.log(sideName + " is no longer valid")
            state.sides[sideName].neighborIsValid = False
            return
        state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
        state.sides[sideName].sideState = firmware.SideState.EXPECTING_NUM_TILES
        return

    elif ([message] == firmware.NO_MESSAGE):
        #tile.log(sideName + " received no")
        if ((state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS and state.tile_state.tileState != firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES) or state.tile_state.parentName == sideName):
            tile.log(sideName + " is no longer valid")
            state.sides[sideName].neighborIsValid = False
            return
        state.sides[sideName].sideState = firmware.SideState.NOT_CHILD

    elif ([message] == firmware.AWAKE_MESSAGE):
        #tile.log(sideName + " received awake")
        return

    else:
        tile.log(sideName + " received invalid message " + str(message))
        tile.log(sideName + " is no longer valid")
        state.sides[sideName].neighborIsValid = False
        return


def loop(state, tile):
    curr_time = micros()
    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid):
            now = micros()
            if ((sideState.neighborLastHighTime == -1 and state.tile_state.wakeupTime + (TIMEOUT * 2) < now) or (sideState.neighborLastHighTime != -1 and now - sideState.neighborLastHighTime > TIMEOUT)):
                # Neighbor died
                tile.log(sideName + " timed out. last high time: " +
                         str(sideState.neighborLastHighTime) + " current time: " + str(now))
                if (state.sides[sideName].sideState != firmware.SideState.FINISHED_SENDING_TOPOLOGY and state.sides[sideName].sideState != firmware.SideState.NOT_CHILD and state.sides[sideName].sideState != firmware.SideState.UNCONFIRMED_CHILD_STATUS):
                    state.sides[sideName].sideState = firmware.SideState.NOT_CHILD
                tile.log(sideName + " is no longer valid")
                sideState.neighborIsValid = False
                if (state.tile_state.parentName == sideName):
                    tile.log("Parent died, therefore this tile should reset")
                    # Parent died, therefore this tile should reset
                    resetTile(state, tile)
                    tile.sleep()

    # Write bits to sides
    if (state.tile_state.wakeupTime != -1):
        if (state.sides["top"].neighborIsValid and (state.sides["top"].sideState != firmware.SideState.NOT_CHILD or state.tile_state.parentName == "top")):
            #tile.log("Top messages to send: " + str(state.sides["top"].messagesToSend))
            bit = state.sides["top"].getNextBitToSend()
            #tile.log("Top sending bit: " + str(bit))
            if bit > 0:
                firmware.sendPulse(tile.top)
        if (state.sides["bottom"].neighborIsValid and (state.sides["bottom"].sideState != firmware.SideState.NOT_CHILD or state.tile_state.parentName == "bottom")):
            #tile.log("Bottom messages to send: " + str(state.sides["bottom"].messagesToSend))
            bit = state.sides["bottom"].getNextBitToSend()
            #tile.log("Bottom sending bit: " + str(bit))
            if bit > 0:
                firmware.sendPulse(tile.bottom)
        if (state.sides["left"].neighborIsValid and (state.sides["left"].sideState != firmware.SideState.NOT_CHILD or state.tile_state.parentName == "left")):
            #tile.log("Left messages to send: " + str(state.sides["left"].messagesToSend))
            bit = state.sides["left"].getNextBitToSend()
            #tile.log("Left sending bit: " + str(bit))
            if bit > 0:
                firmware.sendPulse(tile.left)
        if (state.sides["right"].neighborIsValid and (state.sides["right"].sideState != firmware.SideState.NOT_CHILD or state.tile_state.parentName == "right")):
            #tile.log("Right messages to send: " + str(state.sides["right"].messagesToSend))
            bit = state.sides["right"].getNextBitToSend()
            #tile.log("Right sending bit: " + str(bit))
            if bit > 0:
                firmware.sendPulse(tile.right)

    # Process pulses
    state.sides["top"].sideMutex.acquire()
    state.sides["right"].sideMutex.acquire()
    state.sides["left"].sideMutex.acquire()
    state.sides["bottom"].sideMutex.acquire()
    if (state.sides["top"].newPulseTimes):
        time_received = state.sides["top"].newPulseTimes.pop(0)
        state.sides["top"].handlePulseReceived(time_received)
    if (state.sides["right"].newPulseTimes):
        time_received = state.sides["right"].newPulseTimes.pop(0)
        state.sides["right"].handlePulseReceived(time_received)
    if (state.sides["left"].newPulseTimes):
        time_received = state.sides["left"].newPulseTimes.pop(0)
        state.sides["left"].handlePulseReceived(time_received)
    if (state.sides["bottom"].newPulseTimes):
        time_received = state.sides["bottom"].newPulseTimes.pop(0)
        state.sides["bottom"].handlePulseReceived(time_received)
    state.sides["top"].sideMutex.release()
    state.sides["right"].sideMutex.release()
    state.sides["left"].sideMutex.release()
    state.sides["bottom"].sideMutex.release()

    # Read messages
    if (state.sides["top"].hasMessage() and state.sides["top"].neighborIsValid):
        processMessage(state, tile, "top", state.sides["top"].getNextMessage())
    elif (state.sides["right"].hasMessage() and state.sides["right"].neighborIsValid):
        processMessage(state, tile, "right", state.sides["right"].getNextMessage())
    elif (state.sides["left"].hasMessage() and state.sides["left"].neighborIsValid):
        processMessage(state, tile, "left", state.sides["left"].getNextMessage())
    elif (state.sides["bottom"].hasMessage() and state.sides["bottom"].neighborIsValid):
        processMessage(state, tile, "bottom", state.sides["bottom"].getNextMessage())

    for (sideName, sideState) in state.sides.items():
        if (sideState.neighborIsValid and sideState.sideState != firmware.SideState.NOT_CHILD and sideState.sideState != firmware.SideState.FINISHED_SENDING_TOPOLOGY):
            # Not ready to forward topology to parent.
            # Delay long enough for next clock cycle
            delayMicros(CLOCK_PERIOD - (micros() - curr_time))
            return

    if (state.tile_state.parentName != None and not state.tile_state.reportedTopology):
        # All neighbors are either not valid, not child, or done sending topology. Ready to forward topology to parent.
        state.ready_to_report = True
        state.tile_state.reportedTopology = True
        # tile.log("Sending topology to parent")
        state.sides[state.tile_state.parentName].enqueueTopology(state.topology)
        state.tile_state.tileState = firmware.TileState.SENDING_TOPOLOGY

    if (state.tile_state.tileState == firmware.TileState.SENDING_TOPOLOGY):
        # Check if tile finished sending topology
        if (len(state.sides[state.tile_state.parentName].messagesToSend) == 0 or state.sides[state.tile_state.parentName].messagesToSend[0] == firmware.AWAKE_MESSAGE):
            tile.log("Done sending topology")
            #resetTile(state, tile)
            # tile.sleep()

            # Delay long enough for next clock cycle
    delayMicros(CLOCK_PERIOD - (micros() - curr_time))
