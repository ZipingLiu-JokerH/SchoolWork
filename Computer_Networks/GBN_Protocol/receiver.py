import sys
from socket import *
from packet import Packet

# Note, expected_seqnum is in mod 32

# read in command line arguments
try:
    host_addr = sys.argv[1]
    send_port = int(sys.argv[2])
    receive_port = int(sys.argv[3])
    transfer_fname = sys.argv[4]
except ValueError:
    print("The second and third arguments should be integer")
    sys.exit(1)


# open the file waiting to writ
f = open(transfer_fname, "w")

# create log files
arrivallog = open("arrival.log", "w")

# create UDP socket
receiver_socket = socket(AF_INET, SOCK_DGRAM)
receiver_socket.bind(("", receive_port))

expected_seqnum = 0

# print("start receiving packets")

while True:
    # print(f"expecting packet seqnum = {expected_seqnum}")

    # receive data prom sender, decode the packet
    dat_packet, sender_addr = receiver_socket.recvfrom(1024)
    pac = Packet.parseUDPdata(dat_packet)

    # we receive a data packet, write the seqnum to arrival.log
    if pac.getType() == 1:
        # print("receive a data packet")
        arrival_line = str(pac.getSeqNum()) + "\n"
        arrivallog.write(arrival_line)

        # if the first packet is lose, we ignore the current iteration, let the sender to handle.
        if expected_seqnum == 0 and pac.getSeqNum() != 0:
            continue

        # if the packet received is the expected one, get the data and write to output file
        if pac.getSeqNum() == expected_seqnum:
            # print(f"received pack is the expected one, extract data, has seqnum = {expected_seqnum}, send ack ={pac.getSeqNum()}")
            f.write(pac.getData().decode())
            ack_packet = Packet.createACK(pac.getSeqNum())
            # increase the expected_seqnumber
            expected_seqnum = (expected_seqnum + 1) % 32
        # packet receive is not the expected one, ignore the packet.
        elif expected_seqnum != 0 and pac.getSeqNum() != expected_seqnum:
            # print(f"received pac is not the expected one, ignore, send ack = {expected_seqnum - 1}")
            ack_packet = Packet.createACK(expected_seqnum - 1)

        # send ack packet to the sender
        udp_ack_packet = ack_packet.getUDPdata()
        receiver_socket.sendto(udp_ack_packet, (host_addr, send_port))

    # we receive a EOT packet from sender, let's send an EOT packet back and exit.
    elif pac.getType() == 2:
        # print("receive an EOT packet, receiver send EOT back")
        EOTpac = Packet.createEOT(pac.getSeqNum())
        receiver_socket.sendto(EOTpac.getUDPdata(), (host_addr, send_port))
        receiver_socket.close()
        f.close()
        break

# print("Receiver closed")