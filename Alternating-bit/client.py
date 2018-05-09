from socket import *
import time
import json


serverName = gethostname()
serverPort = 12005
buffer_size = 2048
prevSeq = 1 #this is set to one so it will initally be the opposite of the ackNum
bytesRcv = 0

clientSocket = socket(AF_INET, SOCK_DGRAM)

filename = input("Enter a filename: ")
print("Requesting " + filename + "...")
clientSocket.sendto(filename.encode(), (serverName, serverPort))
startTime = time.time()

with open("rcv" + filename, 'w') as f:
    while True:
        serverMessage, serverAddress = clientSocket.recvfrom(buffer_size)
        message = json.loads(serverMessage.decode())
        seqNumber = message['SEQ']

        if message['payload']  == "exit":                                       #If this message indicates it is the last packet
            print("File recieved!")
            print("Total time to send file(Alternating-bit): " + str(time.time() - startTime))
            clientSocket.sendto(str(seqNumber).encode(), serverAddress)
            print("closing connection...")
            f.close()
            break

        if seqNumber == prevSeq:                                                    #If the sequence number is same as the previous sequence number
            clientSocket.sendto(str(prevSeq).encode(), serverAddress)               #Resend an ACK message (e.g., this could occur if the ACK message was lost)
        else:
            curTime = time.localtime(time.time())
            curTimeFormated = ( ("0" + str(curTime[3])) if curTime[3] < 10 else str(curTime[3])) + ":" + ( ("0" + str(curTime[4])) if curTime[4] < 10 else str(curTime[4])) + ":" + ( ("0" + str(curTime[5])) if curTime[5] < 10 else str(curTime[5]))
            print("time: " + curTimeFormated + " recieved bytes " + str(bytesRcv) + " to " + str(bytesRcv + len(message['payload'].encode('utf-8')))  )
            bytesRcv += len(message['payload'].encode('utf-8'))
            f.write(message['payload'])
            clientSocket.sendto(str(seqNumber).encode(), serverAddress)
            prevSeq  = seqNumber

clientSocket.close()
