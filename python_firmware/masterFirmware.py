import time
from enum import Enum
import firmware
from firmware import SideStateMachine, TileStateMachine, CLOCK_PERIOD, Message, TIMEOUT
import util
from arduino import micros, delayMicros


def playHandler(state, tile):
    if (state.newAttemptQueued):
        # A new attempt has already been queued. Ignore this button press.
        return

    if (state.tile_state.wakeupTime != -1):
        tile.log("New Play Attempt Queued")
        state.newAttemptQueued = True
    else:
        resetTile(state, tile)
        tile.wakeUp()
        delayMicros(firmware.CLOCK_PERIOD * firmware.WORD_SIZE * 2)
        state.tile_state.wakeupTime = micros()
        tile.log("Play!")
        state.sides["bottom"].enqueueMessage(Message(firmware.WAKE_UP))
        state.sides["bottom"].sentWakeUp = True
        state.sides["bottom"].enqueueMessage(Message(firmware.REQUEST_PARENT_TOP))
        state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
        state.sides["bottom"].sideState = firmware.SideState.UNCONFIRMED_CHILD_STATUS


def bottomInterruptHandler(state, tile, dataHigh):
    time_received = micros()
    if (state.sides["bottom"].neighborIsValid and dataHigh):  # Data is high
        #tile.log("received bottom pulse at {}!".format(time_received))
        if (state.sides["bottom"].sentWakeUp):
            if (not state.sides["bottom"].receivedWakeUp):
                # Side sent wake up signal
                tile.log("bottom" + " got wake up signal")
                state.sides["bottom"].receivedWakeUp = True
            else:
                state.sides["bottom"].handlePulseReceived(time_received)
            state.sides["bottom"].neighborLastHighTime = time_received


def processMessage(state, tile, sideName):
    if (state.sides[sideName].neighborIsValid):
        message = state.sides[sideName].getNextMessage()

        if (state.sides[sideName].sideState == firmware.SideState.UNCONFIRMED_CHILD_STATUS):
            if ([message] == firmware.YES_MESSAGE):
                #tile.log(sideName + " received yes")
                if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS):
                    tile.log("Tilestate is not SENDING_PARENT_REQUESTS. Neighbor is no longer valid.")
                    state.sides[sideName].neighborIsValid = False
                    return
                state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_NUM_TILES
                return
            elif ([message] == firmware.NO_MESSAGE):
                #tile.log(sideName + " received no")
                if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS):
                    state.sides[sideName].neighborIsValid = False
                    return

        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
            if ([message] == firmware.AWAKE_MESSAGE):
                #tile.log(sideName + " received awake")
                return

            numTiles = util.binaryListToUnsignedInt(message[1:-2])
            #tile.log(sideName + " received numTiles: " + str(numTiles))
            state.sides[sideName].numTileInfoExpected = numTiles
            state.sides[sideName].neighborTopology = [
                [0 for i in range(numTiles * 2 - 1)] for j in range(numTiles * 2 - 1)]
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
            state.sides[sideName].neighborTopology[midpoint +
                                                   state.sides[sideName].currYCoordinate][midpoint + state.sides[sideName].currXCoordinate] = encoding
            state.sides[sideName].numTileInfoExpected -= 1
            if (state.sides[sideName].numTileInfoExpected > 0):
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
                return
            else:
                state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
                state.topology = stripTopology(state.sides[sideName].neighborTopology)

                reportTopology(state, tile, sideName)
                return

        if ([message] == firmware.AWAKE_MESSAGE):
            #tile.log(sideName + " received awake")
            return

        else:
            tile.log(sideName + " received invalid message " + str(message) + ". Neighbor is no longer valid.")
            state.sides[sideName].neighborIsValid = False


def stripTopology(topology):
    # Removes completely blank rows and columns

    rowsToDelete = [True for i in range(len(topology))]
    colsToDelete = [True for i in range(len(topology[0]))]
    for i in range(len(topology)):
        for j in range(len(topology[0])):
            if (topology[i][j]) != 0:
                rowsToDelete[i] = False
                colsToDelete[j] = False
    strippedTopology = []
    for i in range(len(topology)):
        if (not rowsToDelete[i]):
            strippedTopology.append([topology[i][j] for j in range(len(topology[i])) if not colsToDelete[j]])
    return strippedTopology


def reportTopology(state, tile, sideName):
    # Ready to report topology
    tile.log("Ready to report topology")
    state.ready_to_report = True
    state.sides[sideName].neighborIsValid = False
    state.tile_state.wakeupTime = -1
    # Do not reset completely, because simulator needs to retrieve tiles
    if (state.newAttemptQueued):
        delayMicros(1000)  # Delay long enough for simulator to retrieve tiles
        playHandler(state, tile)


def resetTile(state, tile):
    tile.log("Resetting tile")
    init(state, tile)


def init(state, tile):
    state.ready_to_report = False

    tile.log("Initializing tile")
    tile.bottom.registerInterruptHandler(lambda: bottomInterruptHandler(state, tile, tile.bottom.readData()))
    tile.registerPlayHandler(lambda: playHandler(state, tile))

    state.topology = [[]]

    state.newAttemptQueued = False

    state.tile_state = TileStateMachine()
    state.sides = {"bottom": SideStateMachine()}

    tile.sleep()


def loop(state, tile):
    if (state.tile_state.wakeupTime != -1):
        curr_time = micros()

        bottomSideState = state.sides["bottom"]
        if (not bottomSideState.neighborIsValid):
            tile.log("Bottom died due to error")
            reportTopology(state, tile, "bottom")
            return
        else:
            now = micros()
            if ((bottomSideState.neighborLastHighTime == -1 and state.tile_state.wakeupTime + (TIMEOUT * 2) < now) or (bottomSideState.neighborLastHighTime != -1 and now - bottomSideState.neighborLastHighTime > TIMEOUT)):
                # Bottom side died
                tile.log("Bottom timed out")
                reportTopology(state, tile, "bottom")
                return

        # Read message
        if (bottomSideState.hasMessage()):
            processMessage(state, tile, "bottom")

        # Write bit to bottom side
        if (bottomSideState.sentWakeUp):
            bit = bottomSideState.getNextBitToSend()
            if bit > 0:
                firmware.sendPulse(tile.bottom)

        delayMicros(CLOCK_PERIOD - (micros() - curr_time))  # Delay long enough for next clock cycle
