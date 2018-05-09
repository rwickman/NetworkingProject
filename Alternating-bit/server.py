from socket import *
import time
import json

serverName = gethostname()
serverPort = 12005
buffer_size = 1024
exitMessage = "exit"
timeoutInterval = 1
estimatedRTT = 0
devRTT = 0
alpha = 0.125
beta =0.25
isDuplicate = False
seqNumber = 0
totalBytesSent = 0
serverSocket = socket(AF_INET, SOCK_DGRAM)
stayOn = True

serverSocket.bind(('', serverPort))

def calculateTimeout(sampleRTT):
    global estimatedRTT
    global devRTT
    estimatedRTT = (1 - alpha) * estimatedRTT + alpha * sampleRTT
    devRTT = (1-beta) * devRTT + beta * abs(sampleRTT - estimatedRTT)
    return estimatedRTT + 4*devRTT

while stayOn:
    file, address = serverSocket.recvfrom(1024)
    print("Request received for file " + str(file.decode()))
    print("Opening file " + str(file.decode()) + "..." )
    f = open(file.decode(), "r")
    l = f.read(buffer_size)
    while True:
        try:

            serverSocket.sendto(json.dumps({'payload' : l, 'SEQ' : seqNumber }).encode(), address)
            curTime = time.localtime(time.time())                                   #Get the current time based on localtime
            curTimeFormated = ( ("0" + str(curTime[3])) if curTime[3] < 10 else str(curTime[3])) + ":" + ( ("0" + str(curTime[4])) if curTime[4] < 10 else str(curTime[4])) + ":" + ( ("0" + str(curTime[5])) if curTime[5] < 10 else str(curTime[5]))
            print("time: " + curTimeFormated + " sent bytes " + str(totalBytesSent) + " to " + str(totalBytesSent + len(l.encode('utf-8')))  )

            startTime = time.time()
            serverSocket.settimeout(timeoutInterval)
            #print('Sent ', l)
            clientMessage, address = serverSocket.recvfrom(buffer_size)
            while  int(clientMessage.decode()) != seqNumber:                        #If not the correct ACK num, then do nothing (or wait for the correct one to be recieved)
                clientMessage, address = serverSocket.recvfrom(buffer_size)

            serverSocket.settimeout(0)                                              #packets was ACKed so turn off the countdown timer

            if not isDuplicate:                                                     #Only calculate the timeout interval if this packet is not a duplicate
                sampleRTT = time.time() - startTime
                timeoutInterval = calculateTimeout(sampleRTT)

            totalBytesSent += len(l.encode('utf-8'))
            l= f.read(buffer_size)                                                  #Read the next chunk of data

            if not l:
                try:
                    print("File sent!")
                    serverSocket.sendto(json.dumps({'payload' :exitMessage,'SEQ' : seqNumber}).encode(), address)
                    msg, a = serverSocket.recvfrom(buffer_size)
                except:
                    pass
                finally:
                    print("closing connection...")
                    f.close()
                    serverSocket.close()
                    stayOn = False
                    break

            seqNumber = (1 if seqNumber == 0 else 0)
            isDuplicate = False
        except timeout:
            timeoutInterval *=2
            isDuplicate =True
