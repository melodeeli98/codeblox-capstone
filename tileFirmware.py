import time
from arduino import micros, delayMicros

CLOCK_PERIOD = 50000  # 50ms
WORD_SIZE = 9
LIVE_BIT = 0
SENDING_BIT = 1
MSG_BIT_0 = 2
MSG_BIT_1 = 3
MSG_BIT_2 = 4
MSG_BIT_3 = 5
MSG_BIT_4 = 6
MSG_BIT_5 = 7
PARITY_BIT = 8


class SideState():
    def __init__(self, tile):
        neighbor_booting = True
        current_clock = 0
        word_cycle = 0
        data_to_write = []  # Array of messages + paritys
        neighbor_sending_msg = False
        data_read = []  # Array of messages
        num_high_bits_read = 0


def leftRequestResend(state):
    state.left_state.data_to_write = [0, 0, 0, 0, 1, 0, 0]


def leftSendOk(state):
    state.left_state.data_to_write = [0, 0, 0, 0, 0, 1, 0]


def leftClockCallback(state, tile):
    ### Rising edge ###
    if (state.left_state.current_clock == 1):
       # Read data
        data_in = tile.left.readData()

        if (state.left_state.neighbor_booting):
            if (data_in == 0):
                # Neighbor finished booting
                state.left_state.neighbor_booting = False
            else:
                return

        # Case on word cycle
        if (state.left.word_cycle == LIVE_BIT):
            if (data_in == 1):
                # Neighbor booting again - reset everything
                state.left_state.word_cycle = 0
                state.left_state.neighbor_booting = True
                state.left_state.data_to_write = []
                state.left_state.data_read = []
                state.left_state.num_high_bits_read = 0
                state.left_state.neighbor_sending_msg = False
        elif (state.left.word_cycle == SENDING_BIT):
            if (data_in == 0):
                # Neighbor sending incoming message
                state.left_state.neighbor_sending_msg = True
        elif (state.left.word_cycle == MSG_BIT_0):
            # Begin reading neighbor message
            state.left.data_read.append([data_in])
            state.left.num_high_bits_read += data_in
        elif (state.left.word_cycle < PARITY_BIT):
            # Continue reading neighbor message
            state.left.data_read[-1].append(data_in)
            state.left.num_high_bits_read += data_in
        else:
            # Check parity
            if (((state.left.num_high_bits_read + data_in) % 2) != 1):
                leftRequestResend(state)
            else:
                leftSendOk(state)
    # TODO add some way to check for "ok" responses before sending new message

    ### Falling edge ###
    else:
        if (state.left_state.neighbor_booting):
            return

        # Increment word cycle
        state.left_state.word_cycle = (
            state.left_state.word_cycle + 1) % WORD_SIZE

        # Case on word cycle
        if (state.left.word_cycle == LIVE_BIT):  # Indicate aliveness
            tile.left.toggleData(0)
        elif (state.left.word_cycle == SENDING_BIT):  # Indicate message incoming
            if (len(state.left_state.data_to_write) > 0):
                tile.left.toggleData(0)
            else:
                tile.left.toggleData(1)
        else:
            if (len(state.left_state.data_to_write) > 0):  # Send message + parity
                tile.left.toggleData(state.left_state.data_to_write[0])
                del state.left_state.data_to_write[0]


def topClockCallback(state, tile):
    pass


def init(state, tile):
    tile.top.registerClockCallback(lambda: topClockCallback(state, tile))
    tile.left.registerClockCallback(lambda: leftClockCallback(state, tile))
    state.tiles = []
    state.ready_to_report = True
    state.left_state = SideState()
    state.top_state = SideState()


def loop(state, tile):
    tile.right.toggleClock()
    tile.bottom.toggleClock()

    if (state.left_state.current_clock == 0 and tile.left.readClock() == 1):
        state.left_state.current_clock = 1
        leftClockCallback(state, tile)

    elif (state.left_state.current_clock == 1 and tile.left.readClock() == 0):
        state.left_state.current_clock = 0
        leftClockCallback(state, tile)

    if (state.top_state.current_clock == 0 and tile.top.readClock() == 1):
        state.top_state.current_clock = 1
        topClockCallback(state, tile)

    elif (state.top_state. current_clock == 1 and tile.top.readClock() == 0):
        state.top_state.current_clock = 0
        topClockCallback(state, tile)

    # toggle clock

    # if falling edge
    #   increment location in word cycle
    #   if data to write
    #       toggle data pin for data
    #   else
    #       if at end of word cycle
    #           toggle data off
    #       else
    #           toggle data on
    # if rising edge
    #   read data

    # sleep until next clock edge
