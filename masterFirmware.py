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
    time_received = micros()
    if (state.sides["bottom"].neighborIsValid and tile.bottom.readData()): # Data is high
        #tile.log("received bottom pulse at {}!".format(time_received))
        #if (state.sides["bottom"].neighborLastHighTime == -1):
            # Bottom is now alive
            #state.sides["bottom"].neighborLastHighTime = time_received
        #else:
        state.sides["bottom"].handlePulseReceived(time_received, "Master")

def resetTile(state, tile):
    tile.log("resetting tile")
    state.tile_state.reset()
    init(state, tile)

def init(state, tile):
    tile.log("initializing")
    tile.bottom.registerInterruptHandler(lambda: bottomInterruptHandler(state, tile))
    tile.registerPlayHandler(lambda: playHandler(state, tile))

    state.topology = []
    state.ready_to_report = False

    state.communicationInProgress = False
    state.newAttemptQueued = False

    state.tile_state = TileStateMachine()
    state.sides = {"bottom": SideStateMachine()}

    tile.sleep()

def processMessage(state, tile, sideName):
    if (state.sides[sideName].neighborIsValid):
        message = state.sides[sideName].getNextMessage()

        if (state.sides[sideName].sideState == firmware.SideState.UNCONFIRMED_CHILD_STATUS):
            if ([message] == firmware.YES_MESSAGE):
                tile.log("yes")
                if (state.tile_state != firmware.TileState.SENDING_PARENT_REQUESTS):
                    state.sides[sideName].neighborIsValid = False
                    return
                state.tile_state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
                state.sides[sideName] = firmware.SideState.EXPECTING_NUM_TILES
            elif ([message] == firmware.NO_MESSAGE):
                tile.log("no")
                if (state.tile_state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS):
                    state.sides[sideName].neighborIsValid = False
                    return
        
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_NUM_TILES):
            if ([message] == firmware.AWAKE_MESSAGE):
                tile.log("awake")
                return

            numTiles = util.binaryListToUnsignedInt(message)
            tile.log("numTiles:", numTiles)
            state.sides[sideName].numTileInfoExpected = numTiles
            state.sides[sideName].neighborTopology = [[-1 for i in range(numTiles * 2 - 1)] for j in range(numTiles * 2 - 1)]
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_X_COORDINATE
            return
        
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_X_COORDINATE):
            xCoordinate = util.binaryListToSignedInt(message)
            tile.log("xCoordinate:", xCoordinate)
            state.sides[sideName].currXCoordinate = xCoordinate
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_Y_COORDINATE
            return
       
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_Y_COORDINATE):
            yCoordinate = util.binaryListToSignedInt(message)
            tile.log("yCoordinate:", yCoordinate)
            state.sides[sideName].currYCoordinate = yCoordinate
            state.sides[sideName].sideState = firmware.SideState.EXPECTING_ENCODING
            return
        
        elif (state.sides[sideName].sideState == firmware.SideState.EXPECTING_ENCODING):
            encoding = util.binaryListToUnsignedInt(message)
            tile.log("encoding:", encoding)
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
        
        if ([message] == firmware.AWAKE_MESSAGE):
            tile.log("awake")
            return

        else:
            tile.log("invalid message")
            state.sides[sideName].neighborIsValid = False

def handleBottomTileDied(state, tile):
    if (state.newAttemptQueued):
        state.newAttemptQueued = False
        resetTile(state, tile)
        playHandler(state, tile)
    else:
        resetTile(state, tile)
        tile.sleep()
        tile.killThread()

def loop(state, tile):
    #next_check_timeout_time = micros() + TIMEOUT
    curr_time = micros()

    bottomSideState = state.sides["bottom"]
    if (not bottomSideState.neighborIsValid):
        tile.log("Bottom side died due to error")
        handleBottomTileDied(state, tile)
        return
    else:
        if (bottomSideState.neighborLastHighTime != -1):
            if (micros() - bottomSideState.neighborLastHighTime > TIMEOUT):
                # Bottom side died
                tile.log("Bottom side timed out")
                handleBottomTileDied(state, tile)
                return
            #else:
                #if (bottomSideState.neighborLastHighTime + TIMEOUT < next_check_timeout_time):
                    #next_check_timeout_time = bottomSideState.neighborLastHighTime + TIMEOUT
        
    # Read message
    if (bottomSideState.hasMessage()):
        processMessage(state, tile, "bottom")
            
    # Write bit to bottom side
    bit = bottomSideState.getNextBitToSend()
    tile.log(bottomSideState.messagesToSend)
    tile.log("Sending " + str(bit))
    if bit > 0:
        firmware.sendPulse(tile.bottom)

    #curr_time = micros()
    #if (next_check_timeout_time - curr_time > 0):
        #delayMicros(next_check_timeout_time - curr_time)
    delayMicros(CLOCK_PERIOD - (micros() - curr_time))