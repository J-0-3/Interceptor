from interceptor.net.protocols.tcp import parse_raw_tcp_packet
from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer3 import l3_recv
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.io as io
import interceptor.db as db

class Module:
    """Passively observes network traffic and adds services to the database when a TCP threeway handshake is observed."""
    def __init__(self):
        self.running = False
    
    def run(self, interface: Interface = get_default_interface(), ignore_unknown_hosts: bool = False):
        db_conn = db.open()
        sock = open_socket(interface)
        self.running = True
        io.write("Beginning service sniffing.")
        while self.running:
            recvd = l3_recv(interface=interface, sock=sock)
            if recvd is None:
                continue
            _, frame, pkt = recvd
            if pkt.src.public:
                continue
            if pkt.proto == 6:
                tcp_pkt = parse_raw_tcp_packet(pkt.payload)
                if tcp_pkt.syn and tcp_pkt.ack:
                    host = db.search_hosts(db_conn, ipv4_addr=pkt.src)
                    if host is None:
                        if ignore_unknown_hosts:
                            continue
                        host_id = db.add_host(db_conn, ipv4_addr=pkt.src, mac_addr=frame.src)
                        svc_id = db.add_service(db_conn, host_id, "TCP", tcp_pkt.src)
                        io.write(f"Added service {svc_id} ({pkt.src}, {tcp_pkt.src}, TCP)")
                    else:
                        host_id = host.id
                        if db.search_services(db_conn, host_id=host_id, port=tcp_pkt.src, transport_protocol="TCP") is None:
                            svc_id = db.add_service(db_conn, host_id, "TCP", tcp_pkt.src)
                            io.write(f"Added service {svc_id} ({host.ipv4}, {tcp_pkt.src}, TCP)")
                        else:
                            continue

    def stop(self):
        self.running = False