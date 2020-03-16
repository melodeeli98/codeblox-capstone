import time
from arduino import micros, delayMicros
import firmware
from firmware import SideStateMachine, TileStateMachine, TIMEOUT, CLOCK_PERIOD, Message

def topInterruptHandler(state, tile):
    if (state.sides["top"].neighborIsValid and tile.top.readData()): # Data is high
        time_received = micros()
        tile.log("received top pulse at {}!".format(time_received))
        if (state.sides["top"].neighborLastHighTime == -1):
            # Top is now alive
            state.sides["top"].neighborLastHighTime = time_received
            # Send wakeup messages to other sides
            state.sides["left"].enqueueMessage(Message(False, [firmware.WAKE_UP]))
            state.sides["right"].enqueueMessage(Message(False, [firmware.WAKE_UP]))
            state.sides["bottom"].enqueueMessage(Message(False, [firmware.WAKE_UP]))
        else:
            state.sides["top"].handlePulseReceived(time_received)

def leftInterruptHandler(state, tile):
    if (state.sides["left"].neighborIsValid and tile.left.readData()): # Data is high
        tile.log("received left pulse!")

def rightInterruptHandler(state, tile):
    if (state.sides["right"].neighborIsValid and tile.right.readData()): # Data is high
        tile.log("received right pulse!")

def bottomInterruptHandler(state, tile):
    if (state.sides["bottom"].neighborIsValid and tile.bottom.readData()): # Data is high
        tile.log("received bottom pulse!")

def resetTile(state, tile):
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

    state.tiles = []
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

def processMessage(state, tile, sideName):
    if (state.sides[sideName].neighborIsValid):
        message = state.sides[sideName].getNextMessage()

        # TODO put topology receiving logic here

        if (message == firmware.REQUEST_PARENT_TOP):
            if (state.tileState != firmware.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
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
            state.tileState.parentName = "top"
            # Send parent request to neighbors
            state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_TOP]))
            state.sides["right"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_LEFT]))
            state.sides["left"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_RIGHT]))

        elif (message == firmware.REQUEST_PARENT_LEFT):
            if (state.tileState != firmware.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
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
            state.tileState.parentName = "left"
            # Send parent request to neighbors
            state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_TOP]))
            state.sides["right"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_LEFT]))
            state.sides["top"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_BOTTOM]))    

        elif (message == firmware.REQUEST_PARENT_BOTTOM):
            if (state.tileState != firmware.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
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
            state.tileState.parentName = "bottom"
            # Send parent request to neighbors
            state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["left"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_RIGHT]))
            state.sides["right"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_LEFT]))
            state.sides["top"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_BOTTOM]))  

        elif (message == firmware.REQUEST_PARENT_RIGHT):
            if (state.tileState != firmware.WAITING_FOR_PARENT_REQUEST):
                # Tile already has a parent
                state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
                return
            # Say yes to parent
            state.sides[sideName].enqueueMessage(Message(True, [firmware.NO_MESSAGE]))
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
            state.tileState.parentName = "right"
            # Send parent request to neighbors
            state.tileState = firmware.TileState.SENDING_PARENT_REQUESTS
            state.sides["bottom"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_TOP]))
            state.sides["left"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_RIGHT]))
            state.sides["top"].enqueueMessage(Message(True, [firmware.REQUEST_PARENT_BOTTOM]))

        elif (message == firmware.YES_MESSAGE):
            if (state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tileState.parentName == sideName or (sideName in state.tileState.childrenNamesToSendTopology)):
                state.sides[sideName].neighborIsValid = False
                return
            state.tileState = firmware.TileState.WAITING_FOR_CHILD_TOPOLOGIES
            state.tileState.childrenNamesToSendTopology += [sideName]

        elif (message == firmware.NO_MESSAGE):
            if (state.tileState != firmware.TileState.SENDING_PARENT_REQUESTS or state.tileState.parentName == sideName or (sideName in state.tileState.childrenNamesToSendTopology)):
                state.sides[sideName].neighborIsValid = False
                return

        elif (message == firmware.AWAKE_MESSAGE):
            return

        else:
            state.sides[sideName].neighborIsValid = False

def loop(state, tile):
    next_check_timeout_time = micros() + TIMEOUT
    for side in state.sides.items():
        if (side.neighborIsValid):
            if (micros() - side[1].neighborLastHighTime > TIMEOUT):
                # Neighbor died
                del state.sides[side[0]]
                if (state.tile_state.parent == side[0]):
                    # Parent died, therefore this tile should reset
                    resetTile(state, tile)
                    tile.sleep()
            else:
                if (side[1].neighborLastHighTime + TIMEOUT < next_check_timeout_time):
                    next_check_timeout_time = side[1].neighborLastHighTime + TIMEOUT

    if (state.sides["top"].hasMessage()):
        processMessage(state, tile, "top")
    elif (state.sides["right"].hasMessage()):
        processMessage(state, tile, "right")
    elif (state.sides["left"].hasMessage()):
        processMessage(state, tile, "left")
    elif (state.sides["bottom"].hasMessage()):
        processMessage(state, tile, "bottom")
    
    delayMicros(next_check_timeout_time - micros())
