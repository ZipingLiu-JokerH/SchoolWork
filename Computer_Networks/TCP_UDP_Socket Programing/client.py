import sys
from socket import *

# Command line Argument checking
try:
    server_address = sys.argv[1]
    n_port = int(sys.argv[2])
    req_code = int(sys.argv[3])
    msg = sys.argv[4]
except ValueError:
    print("The second and third arguments should be integer")
    sys.exit(1)

# create TCP socket for server, at aerver address and n_port
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((server_address, n_port))
# send the request code to the server
clientSocket.send(str(req_code).encode())
# receive the r_port server send back
r_port = clientSocket.recv(1024).decode()
# close the TCP connection
clientSocket.close()
# check if client provide the correct request code or not.
# In the case of wrong request code, the client will not receive anything from the server,
# hence an empty string is compared
if r_port == '':
    print("client provide wrong req_code")
    sys.exit(1)

# print(f"Client receive r_port = {r_port}")

# After receiving the r_port, create an UDP socket
Trans_clientSocket = socket(AF_INET, SOCK_DGRAM)
# send the msg to the server's r_port using the UDP socket
Trans_clientSocket.sendto(msg.encode(), (server_address, int(r_port)))
# receive the modified msg from the server, print out and exit.
modifiedmsg, serverAddress = Trans_clientSocket.recvfrom(1024)
print(modifiedmsg.decode())
Trans_clientSocket.close()
