class Packet:
    maxDataLength = 500
    SeqNumModulo = 32

    # Constructors
    def __init__(self, Type, SeqNum, strData):
        if len(strData) > self.maxDataLength:
            raise Exception("Data too large (max 500 char)")
        self.type = Type
        self.seqnum = SeqNum % self.SeqNumModulo
        self.data = strData

    # special packet constructors to be used in place of hidden constructor
    @staticmethod
    def createACK(SeqNum):
        return Packet(0, SeqNum, "")

    @staticmethod
    def createPacket(SeqNum, data):
        return Packet(1, SeqNum, data)

    @staticmethod
    def createEOT(SeqNum):
        return Packet(2, SeqNum, "")

    # packet Data

    def getType(self):
        return self.type

    def getSeqNum(self):
        return self.seqnum

    def getLength(self):
        return len(self.data)

    def getData(self):
        return self.data.encode()

    # UDP helpers
    def getUDPdata(self):
        array = bytearray()
        array.extend(self.type.to_bytes(length=4, byteorder="big"))
        array.extend(self.seqnum.to_bytes(length=4, byteorder="big"))
        array.extend(len(self.data).to_bytes(length=4, byteorder="big"))
        array.extend(self.data.encode())
        return array

    @staticmethod
    def parseUDPdata(UDPdata):
        type = int.from_bytes(UDPdata[0:4], byteorder="big")
        seqnum = int.from_bytes(UDPdata[4:8], byteorder="big")
        length = int.from_bytes(UDPdata[8:12], byteorder="big")
        data = UDPdata[12:12+length].decode()
        return Packet(type, seqnum, data)
