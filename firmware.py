from enum import Enum
import util

#CLOCK_PERIOD = 500000  # 500000us (0.5 sec)
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
TIMEOUT = CLOCK_PERIOD * WORD_SIZE * 2

WAKE_UP = [[1, 0, 0, 0, 0, 0, 0]]

REQUEST_PARENT_TOP = [[1] + [1, 0, 0, 0, 0, 1] + [1] + [1]]
REQUEST_PARENT_RIGHT = [[1] + [1, 0, 0, 0, 1, 0] + [1] + [1]]
REQUEST_PARENT_BOTTOM = [[1] + [1, 0, 0, 1, 0, 0] + [1] + [1]]
REQUEST_PARENT_LEFT = [[1] + [1, 0, 1, 0, 0, 0] + [1] + [1]]
REQUEST_RESEND_MESSAGE = [[1] + [0, 0, 0, 1, 0, 0] + [0] + [1]]
YES_MESSAGE = [[1] + [0, 0, 0, 0, 1, 0] + [0] + [1]]
NO_MESSAGE = [[1] + [0, 0, 0, 0, 0, 1] + [0] + [1]]
AWAKE_MESSAGE = [[1] + [0, 0, 0, 0, 0, 0] + [1] + [1]]

def sendPulse(side):
    side.toggleData()
    side.toggleData()

class TileStateMachine:
    def __init__(self):
        self.parentName = None
        self.tileState = TileState.WAITING_FOR_PARENT_REQUEST
        self.reportedTopology = False

    def reset(self):
        self.__init__()

class Message:
    def __init__(self, isResendable, messages):
        self.isResendable = isResendable
        self.messages = messages
        self.messageIndex = 0
        self.bitIndex = 0
    
    def __repr__(self):
        return "Message: " + str(self.messages)

class TileState(Enum):
    WAITING_FOR_PARENT_REQUEST = 1
    SENDING_PARENT_REQUESTS = 2
    WAITING_FOR_CHILD_TOPOLOGIES = 3

class SideState(Enum):
    UNCONFIRMED_CHILD_STATUS = 1
    NOT_CHILD = 2
    EXPECTING_NUM_TILES = 3
    EXPECTING_X_COORDINATE = 4
    EXPECTING_Y_COORDINATE = 5
    EXPECTING_ENCODING = 6
    FINISHED_SENDING_TOPOLOGY = 7

class SideStateMachine:
    def __init__(self):
        self.neighborIsValid = True # if communication failure occurs, tile will shut down all communication with this neighbor even if it's awake.
        self.messagesToSend = []
        #self.messageSent = Message(True, [[]])
        self.neighborLastHighTime = -1
        self.messageStartTime = -1
        self.currBitsRead = []
        self.messagesRead = []
        self.sideState = SideState.UNCONFIRMED_CHILD_STATUS
        self.numTileInfoExpected = 0
        self.currXCoordinate = -1
        self.currYCoordinate = -1
        self.neighborTopology = []

    def reset(self):
        self.__init__()
    
    def enqueueTopology(self, topology):
        messages = [0]
        midpoint = len(topology) // 2
        numTiles = 0
        for i in range(len(topology)):
            for j in range(len(topology)):
                if (topology[i][j] != -1):
                    numTiles += 1
                    # x coordinate
                    messages.append([char for char in util.intToSignedBinaryMessage(j - midpoint)])
                    # y coordinate
                    messages.append([char for char in util.intToSignedBinaryMessage(i - midpoint)])
                    # Encoding
                    messages.append([char for char in util.intToUnsignedBinaryMessage(topology[i][j])])
        messages[0] = util.intToUnsignedBinaryMessage(numTiles)
        print("TOPOLOGY:", messages)
        self.enqueueMessage(Message(True, messages))

    def enqueueMessage(self, message):
        self.messagesToSend.append(message)

    def getNextBitToSend(self):
        if not self.messagesToSend:
            self.messagesToSend.append(Message(True, AWAKE_MESSAGE))

        # Get bit to send
        message = self.messagesToSend[0]
        bit = message.messages[message.messageIndex][message.bitIndex]
        #self.messageSent.messages[-1] += [bit]

        # Update indexes
        if (message.bitIndex == len(message.messages[message.messageIndex]) - 1):
            message.bitIndex = 0
            message.messageIndex += 1
        else:
            message.bitIndex += 1

        if (message.messageIndex == len(message.messages)):
            # Done sending current message; remove from list
            self.messagesToSend.pop(0)

        return bit

    def handlePulseReceived(self, time_received, name):
        self.neighborLastHighTime = time_received
        if (self.messageStartTime == -1):
            print(name + ": pulse at word cycle 0")
            # A new message has begun
            self.messageStartTime = time_received
            self.currBitsRead = [1]
        else:
            wordCycle = SideStateMachine.getWordCycle(self.messageStartTime, time_received)
            print(name + ": pulse at word cycle", wordCycle)
            if (wordCycle == -1):
                self.neighborIsValid = False
                #self.enqueueMessage(Message(True, REQUEST_RESEND_MESSAGE))
            elif (wordCycle < len(self.currBitsRead)):
                # Received multiple pulses within cycle. Request resend.
                self.neighborIsValid = False
                print(name + ": two pulses within a cycle")
                #self.enqueueMessage(Message(True, REQUEST_RESEND_MESSAGE))
            else:
                for i in range(len(self.currBitsRead), wordCycle):
                    self.currBitsRead.append(0)
                self.currBitsRead.append(1)

                print(name + ": currBitsRead", self.currBitsRead)

                if (wordCycle == WORD_SIZE):
                    # End of word cycle. Check parity and update state machine for message.
                    highBitCount = 0
                    message = self.currBitsRead[1:-2]
                    parity = self.currBitsRead[-2]
                    for i in range(len(message)):
                        highBitCount += message[i]
                    if (int((highBitCount + parity) % 2) != 1):
                        print(name + ": invalid message from parity")
                        self.neighborIsValid = False
                        #self.enqueueMessage(Message(True, REQUEST_RESEND_MESSAGE))
                    else:
                        #print(name + ": self.messagesRead", self.messagesRead)
                        self.messagesRead += [self.currBitsRead]
                    self.messageStartTime = -1

    def hasMessage(self):
        return len(self.messagesRead) > 0

    def getNextMessage(self):
        return self.messagesRead.pop(0)

    @staticmethod
    def getWordCycle(messageStartTime, time_received):
        if (time_received < messageStartTime + 0.5 * CLOCK_PERIOD):
            return 0

        for i in range(WORD_SIZE - 1):
            if ((time_received >= messageStartTime + (0.5 + i) * CLOCK_PERIOD) and (time_received < messageStartTime + (1.5 + i) * CLOCK_PERIOD)):
                return i + 1
        
        return WORD_SIZE