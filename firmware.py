from enum import Enum

# CLOCK_PERIOD = 50000  # 50000us
CLOCK_PERIOD = 1000000  # 1 sec
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
TIMEOUT = CLOCK_PERIOD * WORD_SIZE

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

class TileStateMachine:
    def __init__(self):
        self.parentName = None
        self.tileState = TileState.WAITING_FOR_PARENT_REQUEST
        self.childrenNamesToSendTopology = []

class Message:
    def __init__(self, isResendable, messages):
        self.isResendable = isResendable
        self.messages = messages
        self.messageIndex = 0
        self.bitIndex = 0

class TileState(Enum):
    WAITING_FOR_PARENT_REQUEST = 1
    SENDING_PARENT_REQUESTS = 2
    WAITING_FOR_CHILD_TOPOLOGIES = 3

class SideState(Enum):
    NOT_EXPECTING_TOPOLOGY = 1
    EXPECTING_NUM_TILES = 2
    EXPECTING_X_COORDINATE = 3
    EXPECTING_Y_COORDINATE = 4
    EXPECTING_ENCODING = 5

class SideStateMachine:
    def __init__(self):
        self.neighborIsValid = True # if communication failure occurs, tile will shut down all communication with this neighbor even if it's awake.
        self.messagesToSend = []
        self.messageSent = Message(True, [[]])
        self.neighborLastHighTime = -1
        self.messageStartTime = -1
        self.currBitsRead = []
        self.messagesRead = []
        self.sideState = SideState.NOT_EXPECTING_TOPOLOGY

    def enqueueMessage(self, message):
        self.messagesToSend.append(message)

    def getNextBitToSend(self):
        if not self.messagesToSend:
            self.messagesToSend.append(Message(True, AWAKE_MESSAGE))

        # Get bit to send
        message = self.messagesToSend[0]
        bit = message.messages[message.messageIndex][message.bitIndex]
        self.messageSent.messages[-1] += [bit]

        # Update indexes
        if (message.bitIndex == len(message.messages[message.messageIndex] - 1)):
            message.bitIndex = 0
            message.messageIndex += 1

        if (message.messageIndex == len(message.messages)):
            # Done sending current message; remove from list
            self.messagesToSend.pop(0)
        
        return bit

    def handlePulseReceived(self, time_received):
        if (self.messageStartTime == -1):
            # A new message has begun
            self.messageStartTime = time_received
            self.currBitsRead = [1]
        else:
            wordCycle = SideStateMachine.getWordCycle(self.messageStartTime, time_received)
            if (wordCycle == -1):
                self.neighborIsValid = False
                #self.enqueueMessage(Message(True, [REQUEST_RESEND_MESSAGE]))
            elif (wordCycle < len(self.currBitsRead)):
                # Received multiple pulses within cycle. Request resend
                self.neighborIsValid = False
                #self.enqueueMessage(Message(True, [REQUEST_RESEND_MESSAGE]))
            else:
                for i in range(len(self.currBitsRead, wordCycle)):
                    self.currBitsRead.append(0)
                self.currBitsRead.append(1)
                if (wordCycle == WORD_SIZE):
                    # Message is done. Check parity and update state machine
                    highBitCount = 0
                    for i in range(len(self.currBitsRead) - 1):
                        highBitCount += self.currBitsRead[i]
                    if (highBitCount + self.currBitsRead[-1] % 2 != 1):
                        self.neighborIsValid = False
                        #self.enqueueMessage(Message(True, [REQUEST_RESEND_MESSAGE]))
                    else:
                        self.messagesRead = self.currBitsRead if (len(self.messagesRead) == 0) else self.messagesRead.append(self.currBitsRead)

    def hasMessage(self):
        return len(self.messagesRead) > 0

    def getNextMessage(self):
        return self.messagesRead.pop(0)

    @staticmethod
    def getWordCycle(self, messageStartTime, time_received):
        for i in range(WORD_SIZE - 1):
            if ((time_received >= messageStartTime + 0.5 + i) and (time_received < messageStartTime + 1.5 + i)):
                return i + 1
        return -1