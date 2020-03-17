import time
from arduino import micros, delayMicros
from enum import Enum
import firmware
from firmware import SideStateMachine, TileStateMachine, CLOCK_PERIOD, Message, TIMEOUT

def playHandler(state, tile):
    if (state.communicationInProgress):
        tile.log("New Play Attempt Queued")
        state.newAttemptQueued = True
    else:
        state.communicationInProgress = True
        tile.log("Play!")
        state.sides["bottom"].enqueueMessage(Message(False, firmware.WAKE_UP))
        state.sides["bottom"].enqueueMessage(Message(True, firmware.REQUEST_PARENT_TOP))
        state.tile_state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
        state.sides["bottom"].sideState = firmware.SideState.UNCONFIRMED_CHILD_STATUS

def bottomInterruptHandler(state, tile):
    tile.log("received bottom pulse!")

def resetTile(state, tile):
    state.tile_state.reset()
    init(state, tile)

def init(state, tile):
    tile.log("initializing")
    tile.bottom.registerInterruptHandler(
        lambda: bottomInterruptHandler(state, tile))
    tile.registerPlayHandler(lambda: playHandler(state, tile))

    state.topology = []
    state.ready_to_report = True

    state.communicationInProgress = False
    state.newAttemptQueued = False

    state.tile_state = TileStateMachine()
    state.sides = {"bottom": SideStateMachine()}

    tile.sleep()

def processMessage(state, tile, sideName):
    if (state.sides[sideName].neighborIsValid):
        message = state.sides[sideName].getNextMessage()

        if (state.sides[sideName].sideState == firmware.SideState.UNCONFIRMED_CHILD_STATUS):
            if (message == firmware.YES_MESSAGE):
                if (state.tile_state != firmware.TileState.SENDING_PARENT_REQUESTS):
                    state.sides[sideName].neighborIsValid = False
                    return
                state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
                state.sides[sideName] = firmware.SideState.EXPECTING_NUM_TILES
            elif (message == firmware.NO_MESSAGE):
                if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS):
                    state.sides[sideName].neighborIsValid = False
                    return
        
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
            numTiles = util.binaryListToUnsignedInt(message)
            state.sides[sideName].numTileInfoExpected = numTiles
            state.sides[sideName].neighborTopology = [[-1 for i in range(numTiles * 2 - 1)] for j in range(numTiles * 2 - 1)]
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
            state.sides[sideName].neighborTopology[midpoint + state.sides[sideName].currYCoordinate][midpoint + state.sides[sideName].currXCoordinate] = encoding
            state.sides[sideName].numTileInfoExpected -= 1
            if (state.sides[sideName].numTileInfoExpected > 0):
                state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
            else:
                state.sides[sideName].sideState = firmware.SideState.FINISHED_SENDING_TOPOLOGY
                state.topology = state.sides[sideName].neighborTopology
                
                # Ready to report topology
                state.ready_to_report = True
                return
        
        elif (message == firmware.AWAKE_MESSAGE):
            return

        else:
            state.sides[sideName].neighborIsValid = False

def handleBottomTileDied(state, tile):
    if (state.newAttemptQueued):
        state.newAttemptQueued = False
        resetTile(state, tile)
        playHandler(state, tile)
    else:
        resetTile(state, tile)
        tile.sleep()

def loop(state, tile):
    next_check_timeout_time = micros() + TIMEOUT
    bottomSideState = state.sides["bottom"]
    if (not bottomSideState.neighborIsValid):
        handleBottomTileDied(state, tile)
    else:
        if (micros() - bottomSideState.neighborLastHighTime > TIMEOUT):
            # Bottom side died
            handleBottomTileDied(state, tile)
            return
        else:
            if (bottomSideState.neighborLastHighTime + TIMEOUT < next_check_timeout_time):
                next_check_timeout_time = bottomSideState.neighborLastHighTime + TIMEOUT
    
        # Read message
        if (bottomSideState.hasMessage()):
            processMessage(state, tile, "bottom")
        
        # Write bit to bottom side
        bit = bottomSideState.getNextBitToSend()
        if bit > 0:
            firmware.sendPulse(tile.bottom)

        curr_time = micros()
        if (next_check_timeout_time - curr_time > 0):
            delayMicros(next_check_timeout_time - curr_time)