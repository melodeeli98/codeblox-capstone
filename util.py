def binaryStringToInt(s):
    num = 0
    for i in range(len(s[1:])):
        num = num + int(s[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if s[0] == "1" else num

def messageListToUnsignedInt(l):
    num = 0
    for i in range(len(l)):
        num = num + int(l[i + 1])
        num = num * 2
    num = int(num / 2)
    return num

def messageListToSignedInt(l):
    num = 0
    for i in range(len(l[1:])):
        num = num + int(l[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if l[0] == 1 else num

def intToSignedBinaryString(num):
    s = "{0:05b}".format(abs(num))
    if (num < 0):
        return "1" + s
    else:
        return "0" + s

def intToUnsignedBinaryString(num):
    return "{0:06b}".format(num)

def intToSignedBinaryList(num):
    return [char for char in intToSignedBinaryString(num)]

def intToUnsignedBinaryList(num):
    return [char for char in intToUnsignedBinaryString(num)]