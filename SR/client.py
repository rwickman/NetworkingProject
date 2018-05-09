from socket import *
import time, json


serverName = gethostname()
serverPort = 12006
buffer_size = 2048
bytesRcv = 0

winSize = 6
rcv_base = 0

window = {}
#window is of size N, it will contain the packets that have been:
#(1) Expected to recieved
#(2)Out of order but already ACK'd
#(3)Acceptable within window (haven't ACK) at the end of the window/buffer_size


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
        # print("SeqNum Recieved: " + str(seqNumber))
        if message['payload']  == "exit":                                      #If this message indicates it is the last packet
            while rcv_base in window:
                f.write(window[rcv_base])
                rcv_base += 1
            print("File recieved!")
            print("Total time to send file(SR): " + str(time.time() - startTime))
            clientSocket.sendto(str(seqNumber).encode(), serverAddress)
            print("Closing connection...")
            f.close()
            break
        # print("Current rcv_base: " + str(rcv_base))
        if seqNumber >= rcv_base - winSize and seqNumber <= rcv_base -1:                                                    #If the sequence number is same as the previous sequence number
            clientSocket.sendto(str(seqNumber).encode(), serverAddress)               #Resend an ACK message (e.g., this could occur if the ACK message was lost)
        elif seqNumber >= rcv_base and seqNumber <= rcv_base + winSize -1:
            clientSocket.sendto(str(seqNumber).encode(), serverAddress)                 #ACK message, bytesRcv is ACK number
            if seqNumber not in window:
                window[seqNumber] = message['payload']
                curTime = time.localtime(time.time())
                curTimeFormated = ( ("0" + str(curTime[3])) if curTime[3] < 10 else str(curTime[3])) + ":" + ( ("0" + str(curTime[4])) if curTime[4] < 10 else str(curTime[4])) + ":" + ( ("0" + str(curTime[5])) if curTime[5] < 10 else str(curTime[5]))
                print("time: " + curTimeFormated + " recieved bytes " + str(bytesRcv) + " to " + str(bytesRcv + len(message['payload'].encode('utf-8'))) + ", #" + str(seqNumber)  )
                bytesRcv += len(message['payload'].encode('utf-8'))
                while rcv_base in window:
                    f.write(window[rcv_base])
                    rcv_base += 1

clientSocket.close()
