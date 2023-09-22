from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer3 import l3_recv, l3_send
from interceptor.net.sockets.layer2 import l2_send
from interceptor.net.filters import compile_filter
from interceptor.net.interfaces import Interface, get_default_interface, get_default_gateway_addr
from interceptor.net.protocols.arp import resolve_ip_to_mac
import interceptor.io as io
import interceptor.db as db

class Module:
    """Conditionally forwards IP packets from specified hosts based on destination IP address"""
    def __init__(self):
        self.running = False

    def run(self,
            allow_filter: str = "",
            deny_filter: str = "",
            allow_from: list[int] = None,
            deny_from: list[int] = None,
            interface: Interface = get_default_interface()):
        if allow_filter != "":
            try:
                filter_func = compile_filter(allow_filter)
            except ValueError as exception:
                io.write(f"Cannot compile allow filter: {exception}")
                return False
        elif deny_filter != "":
            try:
                deny_filter_func = compile_filter(deny_filter)
                filter_func = lambda f: not deny_filter_func(f)
            except ValueError as exception:
                io.write(f"Cannot compile deny filter: {exception}")
                return False
        else:
            filter_func = lambda f: False
        db_conn = db.open()
        if allow_from is None:
            if deny_from is None:
                allow_from = db.get_all_hosts(db_conn)
                deny_from = []
            else:
                allow_from = []
                deny_from = [db.get_host(db_conn, i) for i in deny_from]
                while None in deny_from:
                    io.write("Host in deny list not found in database.")
                    deny_from.remove(None)
        else:
            deny_from = []
            allow_from = [db.get_host(db_conn, i) for i in allow_from]
            while None in allow_from:
                io.write("Host in allow list not found in database.")
                allow_from.remove(None)
        deny_ips = list(map(lambda h: h.ipv4, deny_from))
        allow_ips = list(map(lambda h: h.ipv4, allow_from))
        default_gateway_ipv4 = get_default_gateway_addr()
        default_gateway_mac = resolve_ip_to_mac(default_gateway_ipv4, interface)
        sock = open_socket(interface)
        self.running = True
        while self.running:
            incoming = l3_recv(1, interface=interface, sock=sock)
            if incoming is None:
                continue
            _, frame, pkt = incoming
            if pkt.dst == interface.ipv4_addr or pkt.src == interface.ipv4_addr:
                continue
            if pkt.dst.public:
                l2_send(default_gateway_mac, frame.proto, frame.payload, interface, sock=sock)
                continue
            if pkt.dst == interface.ipv4_broadcast:
                l2_send("ff:ff:ff:ff:ff:ff", frame.proto, frame.payload, interface, sock=sock)
                continue
            if pkt.src in deny_ips:
                continue
            if not filter_func(frame) and pkt.src not in allow_ips:
                continue
            l3_send(pkt.dst, pkt.proto, pkt.payload, interface, pkt.src, 1, sock,
                    pkt.dscp, pkt.ecn, pkt.ttl, pkt.identification, pkt.flags,
                    pkt.frag_offset)
            io.write(f"Forwarding {str(pkt)}")
        io.write("Stopping IP forwarding.")

    def stop(self):
        self.running = False