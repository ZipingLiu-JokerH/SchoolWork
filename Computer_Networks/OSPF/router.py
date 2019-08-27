import sys
import struct
from socket import *


NBR_ROUTER = 5


class PKT_HELLO:

    def __init__(self, router_id, link_id):
        self.router_id = router_id
        self.link_id = link_id

    def dat_to_byte(self):
        return struct.pack('<II', self.router_id, self.link_id)

    @staticmethod
    def byte_to_data(byts):
        dat = struct.unpack('<II', byts)
        return PKT_HELLO(dat[0], dat[1])

    def write_log(self, is_send, router):
        action = 'send'
        if not is_send:
            action = 'receive'
        line = f"R{router} {action} a HELLO: router_id {self.router_id} link_id {self.link_id}\n"
        return line


class PKT_LSPDU:

    def __init__(self, sender, router_id, link_id, cost, via):
        self.sender = sender
        self.router_id = router_id
        self.link_id = link_id
        self.cost = cost
        self.via = via

    def dat_to_byte(self):
        return struct.pack('<IIIII', self.sender, self.router_id, self.link_id, self.cost, self.via)

    @staticmethod
    def byte_to_data(byts):
        dat = struct.unpack('<IIIII', byts)
        return PKT_LSPDU(dat[0], dat[1], dat[2], dat[3], dat[4])

    def write_log(self, is_send, router):
        action = 'send'
        if not is_send:
            action = 'receive'
        line =f"R{router} {action} an LS PDU: sender {self.sender}, router_id {self.router_id}, " \
            f"link_id {self.link_id}, cost {self.cost}, via {self.via}\n"
        return line


class PKT_INIT:

    def __init__(self, router_id):
        self.router_id = router_id

    def dat_to_byte(self):
        return struct.pack('<I', self.router_id)

    def write_log(self):
        line = f"R{self.router_id} sends an INIT: router_id {self.router_id}\n"
        return line


class LINK_COST:

    def __init__(self, link, cost):
        self.link = link
        self.cost = cost
    '''
    def dat_to_byte(self):
        return struct.pack('<II', self.link, self.cost)
    '''


class CIRCUIT_DB:

    def __init__(self, nbr_link, linkcosts):
        self.nbr_link = nbr_link
        self.linkcosts = linkcosts

    def dat_to_byte(self):
        bs = struct.pack('<I', self.nbr_link)
        for linkcost in self.linkcosts:
            bs += linkcost.dat_to_byte()
        return bs

    @staticmethod
    def byte_to_data(byts):
        nbr_link = struct.unpack_from('<I', byts, 0)[0]
        circuit_db = CIRCUIT_DB(0, [])
        circuit_db.nbr_link = nbr_link
        for i in range(0, nbr_link):
            dat = struct.unpack_from('<II', byts, i*8 + 4)
            linkcost = LINK_COST(dat[0], dat[1])
            circuit_db.linkcosts.append(linkcost)
        return circuit_db

    def write_log(self, router):
        lines = f"R{router} receive a CIRCUIT_DB: nbr_link {self.nbr_link}\n"
        for i in range(self.nbr_link):
            lines += f"Link {self.linkcosts[i].link}, Cost {self.linkcosts[i].cost}\n"
        return lines + '----------------------------------------\n'


class RIB:

    def __init__(self, router):
        self.router = router
        self.table = dict()
        for i in range(1, NBR_ROUTER+1):
            if i == router:
                self.table[i] = ('local', 0)
            else:
                self.table[i] = ('INIF', float('inf'))

    def update(self, dest, cost, via):
        if cost < self.table[dest][1]:
            self.table[dest] = (via, cost)

    def write_log(self):
        lines = "# RIB\n"
        for key in self.table:
            value = self.table[key]
            if isinstance(value[0], int):
                line = f'R{self.router} -> R{key} -> R{value[0]}, {value[1]}\n'
            else:
                line = f'R{self.router} -> R{key} -> {value[0]}, {value[1]}\n'
            lines += line
        return lines + '----------------------------------------\n'


class LSDB:

    def __init__(self, router):
        self.router = router
        self.table = dict()
        self.reachable = dict()

    def self_init(self, circuit_db):
        self.reachable[self.router] = circuit_db.nbr_link
        for linkcost in circuit_db.linkcosts:
            self.table[(self.router, linkcost.link)] = [linkcost.cost, -1, -1, circuit_db.nbr_link]

    def update(self, sender, router_id, link_id, cost, via, number_neighbour):
        if router_id in self.reachable and (router_id, link_id) not in self.table:
            self.reachable[router_id] += 1
        elif router_id not in self.reachable:
            self.reachable[router_id] = 1
        if (router_id, link_id) not in self.table:
            self.table[(router_id, link_id)] = [cost, sender, via, number_neighbour]

    def write_log(self):
        lines = "# Topology database\n"
        for router in self.reachable:
            lines += f"R{self.router} -> R{router} nbr link {self.reachable[router]}\n"
            for entry in self.table:
                if entry[0] == router:
                    lines += f"R{self.router} -> R{entry[0]} link {entry[1]} cost {self.table[entry][0]}\n"
        return lines + '----------------------------------------\n'


# given the link state data base, find the links of a specific router, links in (link_id, cost) pair
def get_links(lsdb, routerid):
    links = []
    for entry in lsdb.table:
        if entry[0] == routerid:
            links.append((entry[1], lsdb.table[entry][0]))
    return links


# determine if 2 router are adjacent, if it is, return the cost of their shared link, else return inf
def adjacent_cost(router1, router2, router_links):
    r1_links = router_links[router1-1]
    r2_links = router_links[router2-1]
    for link in r1_links:
        if link in r2_links:
            return link[1]
    return float('inf')


# find the neighbour of a given router, return a list of (neighbour_id, link_cost) pair
def find_neighbour(router, router_links):
    neighbours = []
    rest_nodes = [i for i in range(1, NBR_ROUTER + 1) if i != router]
    for node in rest_nodes:
        cost = adjacent_cost(router, node, router_links)
        if cost < float('inf'):
            neighbours.append((node, cost))
    return neighbours


# dijkstra algorithm to find the least cost path. Following the steps given in the slide.
# Also update the rib database for logging.
def dijkstra():
    global lsdb, rib
    source = lsdb.router
    D = {source: 0}
    P = {source: None}
    N = [source]
    router_links = []
    for i in range(1, NBR_ROUTER+1):
        router_links.append(get_links(lsdb, i))

    neighbours = find_neighbour(source, router_links)
    non_neighbours = [j for j in range(1, NBR_ROUTER+1) if j != source]
    for neighbour in neighbours:
        D[neighbour[0]] = neighbour[1]
        P[neighbour[0]] = neighbour[0]
        rib.update(neighbour[0], neighbour[1], neighbour[0])
        non_neighbours.remove(neighbour[0])
    for node in non_neighbours:
        D[node] = float('inf')

    while len(N) < NBR_ROUTER:
        min_cost = (None, float('inf'))
        rest = [j for j in range(1, NBR_ROUTER+1) if j not in N]
        for node in rest:
            if D[node] < min_cost[1]:
                min_cost = (node, D[node])
        w = min_cost[0]
        N.append(w)
        if w is None:
            continue
        w_neighbours = find_neighbour(w, router_links)
        for neighbour in w_neighbours:
            if neighbour[0] not in N:
                D[neighbour[0]] = min(D[neighbour[0]], D[w] + adjacent_cost(w, neighbour[0], router_links))
                P[neighbour[0]] = P[w]
                rib.update(neighbour[0], D[neighbour[0]], P[w])


# read in command line arguments
try:
    routerid = int(sys.argv[1])
    nse_host = sys.argv[2]
    nse_port = int(sys.argv[3])
    router_port = int(sys.argv[4])
except ValueError:
    print("expect the second argument, all should be integer")
    sys.exit(1)

# create log files
routerlog = open(f"router{routerid}.log", "w")

# create UDP socket
router_socket = socket(AF_INET, SOCK_DGRAM)
router_socket.bind(("", router_port))

# send the init packet to Network state Emulator
init_pkt = PKT_INIT(routerid)
router_socket.sendto(init_pkt.dat_to_byte(), (nse_host, nse_port))
routerlog.write(init_pkt.write_log())

# receive circuit database from network state Emulator
circuit_db_bytes, nse_addr = router_socket.recvfrom(2048)
circuit_db = CIRCUIT_DB.byte_to_data(circuit_db_bytes)
routerlog.write(circuit_db.write_log(routerid))
# a list of True/False to determine who have says hello to me.
neighbour_hello = [False] * circuit_db.nbr_link

# Init LSDB
lsdb = LSDB(routerid)
lsdb.self_init(circuit_db)
routerlog.write(lsdb.write_log())

# Init RIB
rib = RIB(routerid)
routerlog.write(rib.write_log())

# send Hello to it's neighbours
for neighbour in circuit_db.linkcosts:
    hello_pkt = PKT_HELLO(routerid, neighbour.link)
    router_socket.sendto(hello_pkt.dat_to_byte(), (nse_host, nse_port))
    routerlog.write(hello_pkt.write_log(True, routerid))

# start receiving packet
while True:
    byts, addr = router_socket.recvfrom(2048)
    # ie: received a Hello Pkt
    if len(byts) == 8:
        hello_pkt = PKT_HELLO.byte_to_data(byts)
        routerlog.write(hello_pkt.write_log(False, routerid))
        # for the one says hello to me, up date the neighbour_hello variable, record this hello for future communication
        for i in range(circuit_db.nbr_link):
            if hello_pkt.link_id == circuit_db.linkcosts[i].link:
                neighbour_hello[i] = True
        # send LSDB to neighbour who says hello
        for entry in lsdb.table:
            if lsdb.table[entry][3] > 0:
                lspdu_pkt = PKT_LSPDU(routerid, entry[0], entry[1], lsdb.table[entry][0], hello_pkt.link_id)
                router_socket.sendto(lspdu_pkt.dat_to_byte(), (nse_host, nse_port))
                routerlog.write(lspdu_pkt.write_log(True, routerid))
                lsdb.table[entry][3] = lsdb.table[entry][3] - 1
    # ie: receive a LSPDU Pkt
    else:
        lspdu_pkt = PKT_LSPDU.byte_to_data(byts)
        if lspdu_pkt.router_id == routerid:  # skip since i am receiving my own information
            continue
        routerlog.write(lspdu_pkt.write_log(False, routerid))
        # add this new info to lsdb
        lsdb.update(lspdu_pkt.sender, lspdu_pkt.router_id, lspdu_pkt.link_id, lspdu_pkt.cost,\
                    lspdu_pkt.via, circuit_db.nbr_link)
        routerlog.write(lsdb.write_log())
        # run dijkstra using the current link state data base
        dijkstra()
        routerlog.write(rib.write_log())

        # inform my neighbour about this new information
        for neighbour in circuit_db.linkcosts:
            # send to neighbour who says hello, not the one send me this new info and check
            # if this info have send repeated time or not
            if neighbour.link != lspdu_pkt.via and lsdb.table[(lspdu_pkt.router_id, lspdu_pkt.link_id)][3] > 0 and\
                    neighbour_hello[circuit_db.linkcosts.index(neighbour)]:
                lspdu_pkt_1 = PKT_LSPDU(routerid, lspdu_pkt.router_id, lspdu_pkt.link_id, lspdu_pkt.cost,\
                                        neighbour.link)
                router_socket.sendto(lspdu_pkt_1.dat_to_byte(), (nse_host, nse_port))
                routerlog.write(lspdu_pkt_1.write_log(True, routerid))
                lsdb.table[(lspdu_pkt.router_id, lspdu_pkt.link_id)][3] -= 1



