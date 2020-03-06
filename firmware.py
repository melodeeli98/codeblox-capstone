
# CLOCK_PERIOD = 50000  # 50000us
CLOCK_PERIOD = 2000000  # 2 sec
MESSAGE_SIZE = 6
WORD_SIZE = MESSAGE_SIZE + 2
AWAKE_BIT = 0
MSG_BIT_0 = 1
MSG_BIT_1 = 2
MSG_BIT_2 = 3
MSG_BIT_3 = 4
MSG_BIT_4 = 5
MSG_BIT_5 = 6
PARITY_BIT = 7

WAKE_UP = [1, 0, 0, 0, 0, 0, 0]
REQUEST_PARENT_TOP = [1] + [1, 0, 0, 0, 0, 1] + [1]
REQUEST_PARENT_RIGHT = [1] + [1, 0, 0, 0, 1, 0] + [1]
REQUEST_PARENT_BOTTOM = [1] + [1, 0, 0, 1, 0, 0] + [1]
REQUEST_PARENT_LEFT = [1] + [1, 0, 1, 0, 0, 0] + [1]
REQUEST_RESEND_MESSAGE = [1] + [0, 0, 0, 1, 0, 0] + [0]
YES_MESSAGE = [1] + [0, 0, 0, 0, 1, 0] + [0]
NO_MESSAGE = [1] + [0, 0, 0, 0, 0, 1] + [0]

AWAKE_MESSAGE = [1] + [0, 0, 0, 0, 0, 0] + [1]


def sendPulse(side):
    side.toggleData()
    side.toggleData()


class SideStateMachine:
    def __init__(self):
        self.messagesToSend = []

    def enqueueMessage(self, message):
        self.messagesToSend.append(message)

    def getNextBitToSend(self):
        if not self.messagesToSend:
            self.messagesToSend.append(AWAKE_MESSAGE)

        message = self.messagesToSend.pop(0)
        bit = message.pop(0)
        if message:
            self.messagesToSend.insert(0, message)
        return bit
