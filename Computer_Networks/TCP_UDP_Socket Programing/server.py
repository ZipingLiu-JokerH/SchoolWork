import sys
from socket import *

# Command line argument checking
try:
    req_code = int(sys.argv[1])
except ValueError:
    print("The argument should be an integer")
    sys.exit(1)


# Create TCP Welcome socket
serverSocket = socket(AF_INET, SOCK_STREAM)
# let's try n_port start from 1234, until find one is free.
n_port = 1234
while True:
    try:
        serverSocket.bind(("", n_port))
        break
    except OSError:
        n_port = n_port + 1

# Server begins listening for incoming TCP request and print out the n_port
serverSocket.listen(1)
print(f"SERVER_PORT={n_port}")
# print("The server is ready to receive")

# Always on server
while True:
    # server waits on accept() for incoming request, new socket created on return
    connectionSocket, addr = serverSocket.accept()
    # read the require code send form client
    client_req_code = connectionSocket.recv(1024).decode()
    # check if the client require code is the same as the server require code.
    # If no the same, close the connection.
    if int(client_req_code) != req_code:
        print("Client provide Wrong req_code")
        connectionSocket.close()
    # if the same, server create an UDP socket for later use of msg transfer
    else:
        # print("req_code is correct")
        Trans_serverSocket = socket(AF_INET, SOCK_DGRAM)
        # let's try r_port start from 12345, until find one is free.
        r_port = 12345
        while True:
            try:
                Trans_serverSocket.bind(("",r_port))
                break
            except OSError:
                r_port = r_port + 1
        # print(f"Ready to accept msg, r_port = {r_port}")

        # using the TCP connection socket to send the r_port to the client.
        connectionSocket.send(str(r_port).encode())
        # TCP connection socket finish his job, close.
        connectionSocket.close()
        # receive the client msg from UDP socket which is listing on the r_port.
        msg, clientAddress = Trans_serverSocket.recvfrom(1024)
        # modified the msg and send back to client.
        modifiedmsg = msg.decode()[::-1]
        Trans_serverSocket.sendto(modifiedmsg.encode(), clientAddress)
        # UDP socket finish his job, close.
        Trans_serverSocket.close()     # ************************************************************






