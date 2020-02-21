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

REQUEST_PARENT_MESSAGE = "100000"
REQUEST_RESEND_MESSAGE = "000010"
YES_MESSAGE = "000001"
NO_MESSAGE = "000000"


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
    WAITING_FOR_PARENT_REQUEST = 1
    SENDING_REQUEST_TO_CHILDREN = 2
    WAITING_FOR_TWO_CHILDREN_RESPONSE = 3
    WAITING_FOR_ONE_CHILD_RESPONSE = 4
    RESPONDING_TO_PARENT = 5


class TileState:
    def __init__(self):
        self.parent_side = None
        self.status = TileStatus.WAITING_FOR_PARENT_REQUEST


def queueMessageToSend(side_state, message):
    data = [int(char) for char in message]
    data.append(0 if (sum(data) % 2) == 1 else 1)
    side_state.data_to_write += data


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
    # TODO is this needed?

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
            if (tile_state.status == TileStatus.WAITING_FOR_TWO_CHILDREN_RESPONSE):
                if (side_state.num_tiles_expected > 0):
                    # Child sent too few tiles. Request resend.
                    queueMessageToSend(side_state, REQUEST_RESEND_MESSAGE)
                else:
                    # Child done sending topology.
                    tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE
            elif (tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
                if (side_state.num_tiles_expected > 0):
                    # Child sent too few tiles. Request resend.
                    queueMessageToSend(side_state, REQUEST_RESEND_MESSAGE)
                else:
                    # Child done sending topology.
                    tile_state.status == TileStatus.RESPONDING_TO_PARENT
                    # TODO construct response to parent
    if (side_state.neighbor_sending_messages and side_state.neighbor_word_cycle == LIVE_BIT):
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
    if (side_state.neighbor_sending_messages and side_state.neighbor_word_cycle > LIVE_BIT):
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
            queueMessageToSend(side_state, REQUEST_RESEND_MESSAGE)
        else:
            message = "".join(str(bit) for bit in side_state.data_read)
            updateStateMachine(message, side_state, tile_state, tile)


def updateStateMachine(message, side_state, tile_state, tile):
    if (message == REQUEST_PARENT_MESSAGE):
        if (tile_state.status == TileStatus.WAITING_FOR_PARENT_REQUEST):
            tile_state.parent_side = side_state.name
            queueMessageToSend(side_state, YES_MESSAGE)
            tile_state.status = TileStatus.SENDING_REQUEST_TO_CHILDREN
        else:
            queueMessageToSend(side_state, NO_MESSAGE)
    elif (message == REQUEST_RESEND_MESSAGE):
        # TODO anything else to do here?
        self.next_bit_index_to_write = 0
    elif (message == YES_MESSAGE):
        if (tile_state.status == TileStatus.WAITING_FOR_TWO_CHILDREN_RESPONSE or tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
            side_state.neighbor_is_child = True
            side_state.status = SideStatus.EXPECTING_X_COORDINATE
    elif (message == NO_MESSAGE):
        if (tile_state.status == TileStatus.WAITING_FOR_TWO_CHILDREN_RESPONSE or tile_state.status == TileStatus.WAITING_FOR_ONE_CHILD_RESPONSE):
            side_state.neighbor_is_child = False
            # TODO anything else to do here?
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
                queueMessageToSend(side_state, REQUEST_RESEND_MESSAGE)
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


def binaryStringToInt(s):
    num = 0
    for i in range(len(s[1:])):
        num = num + int(s[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if s[0] == "1" else num


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
            state.left_state, state.tile_state, tile.left.readData(), tile)

    if (state.top_state.read_now):
        readFromSide(
            state.top_side, state.tile_state, tile.top.readData(), tile)
