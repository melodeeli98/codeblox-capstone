import time
from arduino import micros, delayMicros
from enum import Enum

# CLOCK_PERIOD = 50000  # 50000us
CLOCK_PERIOD = 2000000  # 2 sec
WORD_SIZE = 9
MESSAGE_AND_PARITY_SIZE = WORD_SIZE - 2
MESSAGE_SIZE = MESSAGE_AND_PARITY_SIZE - 1
SENDING_BIT = 0
LIVE_BIT = 1
MSG_BIT_0 = 2
MSG_BIT_1 = 3
MSG_BIT_2 = 4
MSG_BIT_3 = 5
MSG_BIT_4 = 6
MSG_BIT_5 = 7
PARITY_BIT = 8

REQUEST_PARENT_MESSAGE = [1, 0, 0, 0, 0, 0]
REQUEST_RESEND_MESSAGE = [0, 0, 0, 0, 1, 0]
YES_MESSAGE = [0, 0, 0, 0, 0, 1]
NO_MESSAGE = [0, 0, 0, 0, 0, 0]

# TODO if send resend and receive resend back, reset and tell neighbor to reset (need reset message)


class SideStatus(Enum):
    NOT_EXPECTING_TILE_INFO = 0
    EXPECTING_TILE_QUANTITY = 1
    EXPECTING_X_COORDINATE = 2
    EXPECTING_Y_COORDINATE = 3
    EXPECTING_SYNTAX_ENCODING = 4


class SideState:
    def __init__(self, name):
        self.name = name
        self.status = SideStatus.NOT_EXPECTING_TILE_INFO
        self.last_high_timestamp = -1
        self.message_start_timestamp = -1
        self.neighbor_word_cycle = 0
        self.next_read_time = -1
        self.read_now = False
        self.neighbor_sending_messages = False
        self.neighbor_alive = False
        self.data_read = []  # 1D array of messages (one bit per element)
        # 1D array of messages + paritys (one bit per element)
        self.data_to_write = []
        self.next_bit_index_to_write = 0
        self.neighbor_is_child = False
        self.num_tiles_expected = 0
        self.curr_x_response = 0
        self.curr_y_response = 0
        self.topology = []


class TileStatus(Enum):
    # Init state, while tile is parentless
    WAITING_FOR_PARENT_REQUEST = 1

    # Sending parent request to bottom and right tiles
    SENDING_REQUEST_TO_CHILDREN = 2

    # Both bottom and right tiles are children. Awaiting both their responses
    WAITING_FOR_TWO_CHILDREN_RESPONSE = 3

    # Only one tile is a child. Awaiting its response
    WAITING_FOR_ONE_CHILD_RESPONSE = 4

    # Tile now has combined topologies. Currently responding to parent
    RESPONDING_TO_PARENT = 5


class TileState:
    def __init__(self):
        self.parent_side = None
        self.status = TileStatus.WAITING_FOR_PARENT_REQUEST
        self.topology = []

# TODO move sending bit to beginning and live bit to the end.


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


def queueMessage(side_state, message):
    message.append(0 if (sum(message) % 2) == 1 else 1)
    side_state.data_to_write += message


def queueTopologyMessage(state):
    data_to_write = []
    topology = state.tile_state.topology
    midpoint = len(topology) // 2
    for i in range(len(topology)):
        for j in range(len(topology)):
            if (topology[i][j] != 0):
                # x coordinate
                data_to_write.append(
                    [char for char in intToSignedBinaryString(j - midpoint)])
                # y coordinate
                data_to_write.append(
                    [char for char in intToSignedBinaryString(i - midpoint)])
                # Encoding
                data_to_write.append(
                    [char for char in intToUnsignedBinaryString(topology[i][j])])


def resetSideState(side_state):
    side_state.status = SideStatus.NOT_EXPECTING_TILE_INFO
    side_state.last_high_timestamp = -1
    side_state.message_start_timestamp = -1
    side_state.next_read_time = -1
    side_state.read_now = False
    side_state.neighbor_sending_messages = False
    side_state.neighbor_alive = False
    side_state.neighbor_word_cycle = 0
    side_state.data_to_write = []
    side_state.next_bit_index_to_write = 0
    side_state.data_read = []
    side_state.neighbor_is_child = False
    side_state.num_tiles_expected = 0
    side_state.curr_x_response = 0
    side_state.curr_y_response = 0
    side_state.topology = []


def checkDataIn(side_state, tile_side, tile_state):
    current_time = micros()
    data_in = tile_side.readData()

    # TODO is this needed?
    # Make sure lines are high at least once per word period
    if (data_in == 1):
        side_state.last_high_timestamp == current_time
        side_state.neighbor_alive = True
    elif ((current_time - side_state.last_high_timestamp) > (WORD_SIZE * CLOCK_PERIOD)):
        # Neighbor is dead. Reset state.
        resetSideState(side_state)
    ###

    # Indicate if it's time to read from lines
    if (side_state.neighbor_word_cycle == SENDING_BIT):
        if (data_in == 0):
            # Either neighbor is dead or message is incoming. For now, assume message is incoming.
            side_state.neighbor_sending_messages = True
            side_state.neighbor_word_cycle = 1
            side_state.message_start_timestamp = current_time
            side_state.next_read_time = current_time + \
                (CLOCK_PERIOD * 1.5)
        else:
            # No longer sending messages
            side_state.neighbor_sending_messages = False
            side_state.data_read = []
    elif (side_state.neighbor_sending_messages and side_state.neighbor_word_cycle == LIVE_BIT):
        if (current_time > side_state.next_read_time):
            if (data_in == 0):
                # Neighbor is dead. Reset state.
                resetSideState(side_state)
            else:
                side_state.neighbor_alive = True
                side_state.neighbor_word_cycle = MSG_BIT_0
                side_state.next_read_time = side_state.message_start_timestamp + \
                    (CLOCK_PERIOD * 0.5) + \
                    (CLOCK_PERIOD * side_state.neighbor_word_cycle)
    elif (side_state.neighbor_sending_messages and side_state.neighbor_word_cycle > LIVE_BIT):
        if (current_time > side_state.next_read_time):
            # Time to read
            if (side_state.neighbor_word_cycle < WORD_SIZE):
                side_state.neighbor_word_cycle += 1
                side_state.read_now = True
                # Set next read time
                side_state.next_read_time = side_state.message_start_timestamp + \
                    (CLOCK_PERIOD * 0.5) + \
                    (CLOCK_PERIOD * side_state.neighbor_word_cycle)
            else:
                # Message done
                side_state.message_start_timestamp = -1
                side_state.next_read_time = -1
                side_state.read_now = False
                side_state.neighbor_word_cycle = 0
        else:
            # Not time to read
            side_state.read_now = False


def readFromSide(side_state, tile_state, read_value, tile):
    if (side_state.neighbor_word_cycle < MSG_BIT_0):
        raise Exception(
            "Trying to read incoming message during sending or live bit")
    elif (side_state.neighbor_word_cycle < PARITY_BIT):
        side_state.data_read.append(read_value)
    else:
        num_high_bits = sum(side_state.data_read[-MESSAGE_SIZE:])
        if ((num_high_bits + read_value) % 2 != 1):
            queueMessage(side_state, REQUEST_RESEND_MESSAGE)
        else:
            message = "".join(str(bit) for bit in side_state.data_read)
            updateStateMachine(message, side_state, tile_state, tile)


def updateStateMachine(message, side_state, tile_state, tile, state):
    if (message == REQUEST_PARENT_MESSAGE):
        if (tile_state.status == TileStatus.WAITING_FOR_PARENT_REQUEST):
            tile_state.parent_side = side_state.name
            queueMessage(side_state, YES_MESSAGE)
            tile_state.status = TileStatus.SENDING_REQUEST_TO_CHILDREN
        else:
            queueMessage(side_state, NO_MESSAGE)
    elif (message == REQUEST_RESEND_MESSAGE):
        # TODO anything else to do here?
        self.next_bit_index_to_write = 0
    elif (message == YES_MESSAGE):
        if (tile_state.status == TileStatus.SENDING_REQUEST_TO_CHILDREN):
            # TODO need mutex for this?
            tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE
            side_state.neighbor_is_child = True
            side_state.status = SideStatus.EXPECTING_X_COORDINATE
        elif (tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
            tile_state.status = TileStatus.WAITING_FOR_TWO_CHILDREN_RESPONSE
            side_state.neighbor_is_child = True
            side_state.status = SideStatus.EXPECTING_X_COORDINATE
        else:
            # Was not expecting this message. Request resend
            queueMessage(side_state, REQUEST_RESEND_MESSAGE)
    elif (message == NO_MESSAGE):
        if (tile_state.status == TileStatus.SENDING_REQUEST_TO_CHILDREN):
            side_state.neighbor_is_child = False
            side_state.status = SideStatus.NOT_EXPECTING_TILE_INFO
        elif (tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
            side_state.neighbor_is_child = False
            side_state.status = SideStatus.NOT_EXPECTING_TILE_INFO
        else:
            # Was not expecting this message. Request resend
            queueMessage(side_state, REQUEST_RESEND_MESSAGE)
    else:
        if (side_state.status == SideStatus.NOT_EXPECTING_TILE_INFO):
            pass
        elif (side_state.status == SideStatus.EXPECTING_TILE_QUANTITY):
            side_state.num_tiles_expected = binaryStringToInt(
                message)
            # Initialize topology with largest possible dimensions and with current tile in the center
            max_topology_size = side_state.num_tiles_expected * 2 + 1
            side_state.topology = [[0 for j in range(max_topology_size
                                                     )] for i in range(max_topology_size)]
            midpoint = side_state.num_tiles_expected
            side_state.topology[midpoint][midpoint] = tile.syntax_map[tile.syntax_name]
            side_state.status = SideStatus.EXPECTING_X_COORDINATE

        elif (side_state.status == SideStatus.EXPECTING_X_COORDINATE):
            if (side_state.num_tiles_expected < 1):
                # Child is sending too many tiles. Request resend.
                queueMessage(side_state, REQUEST_RESEND_MESSAGE)
            side_state.curr_x_response = binaryStringToInt(message)
            side_state.status = SideStatus.EXPECTING_Y_COORDINATE

        elif (side_state.status == SideStatus.EXPECTING_Y_COORDINATE):
            side_state.curr_y_response = binaryStringToInt(message)
            side_state.status = SideStatus.EXPECTING_SYNTAX_ENCODING

        else:  # EXPECTING_SYNTAX_ENCODING
            midpoint = side_state.num_tiles_expected
            side_state.topology[midpoint + side_state.curr_y_response][midpoint +
                                                                       side_state.curr_x_response] = binaryStringToInt(message)
            side_state.num_tiles_expected -= 1
            # Reset sent tile info
            side_state.curr_x_response = 0
            side_state.curr_y_response = 0

    # TODO is this the right way to check when to do this?
    if (not side_state.neighbor_sending_messages):
        # Neighbor finished sending messages
        if (tile_state.status == TileStatus.WAITING_FOR_TWO_CHILDREN_RESPONSE):
            if (side_state.num_tiles_expected > 0):
                # Child sent too few tiles. Request resend.
                queueMessage(side_state, REQUEST_RESEND_MESSAGE)
            else:
                # Child done sending topology.
                tile_state.topology = side_state.topology
                tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE
        elif (tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
            if (side_state.num_tiles_expected > 0):
                # Child sent too few tiles. Request resend.
                queueMessage(side_state, REQUEST_RESEND_MESSAGE)
            else:
                # Child done sending topology. Time to send full topology to parent.
                tile_state.topology = combineTopologies(
                    tile_state.topology, side_state.topology)
                tile_state.status == TileStatus.RESPONDING_TO_PARENT
                queueTopologyMessage(state)


def binaryStringToInt(s):
    num = 0
    for i in range(len(s[1:])):
        num = num + int(s[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if s[0] == "1" else num


def intToSignedBinaryString(num):
    s = "{0:05b}".format(abs(num))
    if (num < 0):
        return "1" + s
    else:
        return "0" + s


def intToUnsignedBinaryString(num):
    return "{0:06b}".format(num)


def init(state, tile):
    state.tiles = []
    state.ready_to_report = True
    state.left_state = SideState("left")
    state.top_state = SideState("top")
    state.tile_state = TileState()


def loop(state, tile):
    checkDataIn(state.left_state, tile.left, state.tile_state)
    checkDataIn(state.top_state, tile.top, state.tile_state)

    if (state.left_state.read_now):
        readFromSide(
            state.left_state, state.tile_state, tile.left.readData(), tile, state)

    if (state.top_state.read_now):
        readFromSide(
            state.top_side, state.tile_state, tile.top.readData(), tile, state)

    # TODO write side logic. Only reset data_to_write when new thing to write is queued up.

# TODO ask left tile to be its parent
