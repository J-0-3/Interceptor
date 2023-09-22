from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer3 import l3_recv
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.io as io
import interceptor.db as db

class Module:
    """Passively observes network traffic and adds observed hosts to the database"""
    def __init__(self):
        self.running = False

    def run(self, interface: Interface = get_default_interface()):
        db_conn = db.open()
        sock = open_socket(interface)
        self.running = True
        io.write("Beginning host sniffing.")
        while self.running:
            received = l3_recv(interface=interface, sock=sock)
            if received is None:
                continue
            _, frame, pkt = received
            for mac, ip in ((frame.src, pkt.src), (frame.dst, pkt.dst)):
                if ip.private and ip != interface.ipv4_broadcast and not ip.multicast:
                    existing_record = db.search_hosts(db_conn, ipv4_addr=ip)
                    if mac != "ff:ff:ff:ff:ff:ff":
                        if existing_record is None:
                            hid = db.add_host(db_conn, ipv4_addr=ip, mac_addr=mac)
                            io.write(f"Added host {hid} ({ip}, {mac})")
                        else:
                            if existing_record.mac is None:
                                db.set_host(db_conn, existing_record.id, mac_addr=mac)
                            elif existing_record.mac != mac:
                                io.write(f"WARNING: MAC address conflict for host {existing_record.id}")
                    else:
                        if existing_record is None:
                            hid = db.add_host(db_conn, ipv4_addr=ip)
                            io.write(f"Added host {hid}.")
        io.write("Stopping host gathering.")

    def stop(self):
        self.running = False
                            