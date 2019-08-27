import sys
import time
import threading
from socket import *
from packet import Packet

# Note: Base and Nextseqnum are not in mod 32, when needed we use %32 to transform them into mod 32.


# receiveACK provide the ability to receive Ack from the receiver and process that Ack
def receiveACK():
    global N, base, nextseqnum, sender_socket, timer, acklog
    # print("sender start receving acks ---- from receiveACK thread")
    while True:
        # receive a packet from the receiver and decode the packet
        ack_packet, reveiver_addr = sender_socket.recvfrom(1024)
        ackpac = Packet.parseUDPdata(ack_packet)
        # print(f"receive ack = {ackpac.seqnum} ---- from receiveACK thread")

        # the packet we get from receiver is EOT packet, All packet has send , sender exit.
        if ackpac.getType() == 2:
            # print("sender receive Receiver's EOT and close ---- from receiveACK thread")
            sender_socket.close()
            break

        # We get an ack packet, write the seqnum into the ack.log file
        ack_line = str(ackpac.seqnum) + "\n"
        acklog.write(ack_line)

        # received ack is useful, we slide the window and reset the timer if needed.
        if base % 32 <= ackpac.getSeqNum():
            # print(f"window base <= reseived ack, reset timer, change base to {ackpac.getSeqNum() + 1}
            # , nextseqnum = {nextseqnum} ---- from receiveACK thread")
            base = (ackpac.getSeqNum() - base % 32 + base) + 1
            if base == nextseqnum:
                timer = -1
            else:
                timer = time.time()

        # otherwise we ignore the ack


# read in command line arguments
try:
    host_addr = sys.argv[1]
    send_port = int(sys.argv[2])
    receive_port = int(sys.argv[3])
    transfer_fname = sys.argv[4]
except ValueError:
    print("The second and third arguments should be integer")
    sys.exit(1)

# read the file content
with open(transfer_fname) as f:
    data = f.read()

# create log files
seqnumlog = open("seqnum.log", "w")
acklog = open("ack.log", "w")

# create packet for all these data
packets = []
for pac in range (0, len(data), 500):
    packets.append(Packet.createPacket(int(pac/500), data[pac:pac+500]))

# print(f"total number of packets = {len(packets)}")

# set up the Window in GBN
N = 10
base = 0
nextseqnum = 0

# create UDP socket
sender_socket = socket(AF_INET, SOCK_DGRAM)
sender_socket.bind(("", receive_port))

# initialize timer, -1 indicate timer is not set
timer = -1

# start the receiveAck thread
ack_thread = threading.Thread(target=receiveACK)
ack_thread.start()

# print("strat sending packet")

# start sending packet
while base < len(packets):
    # check if we are in the window
    if nextseqnum < base + N and nextseqnum < len(packets):
        # print(f"base = {base}, nextseqnum = {nextseqnum} ---- from sending packet thread")
        # we are within the window, ready to send the packet, write seqnum to seqnum.log
        seq_line = str(nextseqnum % 32) + "\n"
        seqnumlog.write(seq_line)

        # get the data packet, incode it and send to receiver
        pac = packets[nextseqnum].getUDPdata()
        sender_socket.sendto(pac, (host_addr, send_port))
        # print(f"send packet # {nextseqnum} ---- from sending packet thread")

        # if base == nextseqnum, we are at the beginning of the window, set the timer
        if base == nextseqnum:
            timer = time.time()
            # print(f"base = nextseqnum, set timer = {timer} ---- from sending packet thread")

        # update nextseqnum
        nextseqnum = nextseqnum + 1

    # the window is full or we are expecting a timeout event.
    elif (timer != -1) and (time.time() - timer > 0.1):
        # print(f"time out, currenttime = {time.time()}, timer = {timer} ---- from sending packet thread")
        # print(f"resend packet from {base} to {nextseqnum} ---- from sending packet thread")

        # reset the timer and resend all packet that is not being acked
        timer = time.time()
        for p in range(base, nextseqnum):
            # print(f"resend packet {p} ---- from sending packet thread")
            seq_line = str(p % 32) + "\n"
            seqnumlog.write(seq_line)
            pac = packets[p].getUDPdata()
            sender_socket.sendto(pac, (host_addr, send_port))


# print("finish sending packets")

# We have successfully send all packets, now send EOT to receiver
last_packet_seqnum = (len(packets) - 1) % 32
EOTpac = Packet.createEOT(1 + last_packet_seqnum)
# print("sender send EOT")
sender_socket.sendto(EOTpac.getUDPdata(), (host_addr, send_port))

ack_thread.join()
seqnumlog.close()
acklog.close()