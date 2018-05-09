from socket import *
import time, json, threading

seqNum = 0
class UDPserver:
    def __init__(self, serverPort, serverName, maxWinSize = 6, buffer_size = 1024):
        self.serverPort = serverPort
        self.serverName = serverName
        self.buffer_size = buffer_size
        self.seqNumber = 0
        self.timeoutInterval = 1
        self.send_base = 0
        self.maxWinSize = maxWinSize
        self.estimatedRTT = 0
        self.devRTT = 0
        self.beta = 0.25
        self.alpha = 0.125
        self.isDuplicate = False
        self.window = {}
        self.acked = {}
        self.winEndPos = 0
        self.totalBytesSent = 0
        self.doneReading = False
        self.exitMessage = "exit"


    def start_connection(self):
        self.serverSocket = socket(AF_INET, SOCK_DGRAM)
        self.serverSocket.bind(('', self.serverPort))
        print("Server ready to recieve...")

    def end_connection(self, clientAddr, seqNum):
        while len(self.window) > self.seqNumber:
            time.sleep(1)

        server.serverSocket.sendto(json.dumps({'payload' :self.exitMessage,'SEQ' : seqNum}).encode(), clientAddr)
        print("File sent!")
        print("Closing connection...")



    def send_datagram(self, clientAddr, seqNum):
        while True:
            try:
                self.serverSocket.sendto(json.dumps({'payload' :self.window[seqNum] , 'SEQ' : seqNum }).encode(), clientAddr)
                self.serverSocket.settimeout(min(self.timeoutInterval, 10))
                startTime = time.time()
                while not self.acked.get(seqNum, False) and self.timeoutInterval+ startTime > time.time():
                    clientMessage, address = self.serverSocket.recvfrom(self.buffer_size)
                    ackNum = json.loads(clientMessage.decode())

                    if not self.isDuplicate:                                                     #Only calculate the timeout interval if this packet is not a duplicate
                        sampleRTT = time.time() - startTime
                        self.timeoutInterval = self.calculateTimeout(sampleRTT)

                    self.acked[ackNum] = True

                    curTime = time.localtime(time.time())                                   #Get the current time based on localtime
                    curTimeFormated = ( ("0" + str(curTime[3])) if curTime[3] < 10 else str(curTime[3])) + ":" + ( ("0" + str(curTime[4])) if curTime[4] < 10 else str(curTime[4])) + ":" + ( ("0" + str(curTime[5])) if curTime[5] < 10 else str(curTime[5]))
                    print("time: " + curTimeFormated + " sent bytes " + str(self.totalBytesSent) + " to " + str(self.totalBytesSent + len(self.window[seqNum].encode('utf-8'))) + ", #" + str(ackNum) )

                if not self.acked.get(seqNum, False):          #If an ack for this packet hasnet been recieved resent the packet
                    raise timeout

                self.totalBytesSent += len(self.window[seqNum].encode('utf-8'))

                self.setSendBase()
                self.isDuplicate = False
                self.seqNumber += 1
                break
            except timeout:
                self.timeoutInterval *=2
                print("timeout for: #" + str(seqNum) + " timeoutInterval: " + str(self.timeoutInterval))
                self.isDuplicate =True


    def calculateTimeout(self, sampleRTT):
        self.estimatedRTT = (1 - self.alpha) * self.estimatedRTT + self.alpha * sampleRTT
        self.devRTT = (1-self.beta) * self.devRTT + self.beta * abs(sampleRTT - self.estimatedRTT)
        return self.estimatedRTT + 4*self.devRTT

    def appendWindow(self, data):
        self.window[self.winEndPos] = data
        self.winEndPos += 1

    def setSendBase(self):
        while self.acked.get(self.send_base, False):
            self.send_base += 1

    def readFromFile(self, filename):
        print("Request received for file " + str(filename))
        print("Opening file " + str(filename) + "..." )
        f = open(filename, "r")
        while True:
            l = f.read(1024)
            if not l:  #This does not work for python3 but works for python2
                print(len(l))
                print(l)
                self.doneReading = True
                break
            self.appendWindow(l)




server = UDPserver(12006, gethostname())
server.start_connection()
file, address = server.serverSocket.recvfrom(1024)
t = threading.Thread(target=server.readFromFile, args=(file.decode(), ))
t.start()

try:
    while True:   #not server.doneReading or seqNum < len(server.window)
        if seqNum >= server.send_base and seqNum <= server.send_base + server.maxWinSize-1 and len(server.window) > seqNum:
            t = threading.Thread(target= server.send_datagram, args=(address,seqNum, ))     #This is what performs the asynchronous tasks by utilizing threading
            t.start()
            seqNum +=1

        if server.doneReading and server.seqNumber >= len(server.window):
            break

    t = threading.Thread(target= server.end_connection, args=(address,seqNum, ))
    t.start()
except KeyboardInterrupt:
    quit()
