from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.addresses import cidr_range, ip_range
import interceptor.net.protocols.arp as arp
import interceptor.threads as threads
import interceptor.db as db
import interceptor.io as io

def _lookup_thread_func(ip_addr, timeout, interface):
    db_conn = db.open()
    arp_pkt = arp.ARPPacket(1, ip_addr)
    io.write(f"Broadcasting ARP request for {ip_addr}")
    reply: arp.ARPPacket = arp_pkt.send_and_recv(interface=interface, timeout_s=timeout)
    if reply is None:
        io.write(f"No reply from {ip_addr}")
    else:
        mac_addr = reply.hwsrc
        io.write(f"{ip_addr} is live at {mac_addr}.")
        db_host = db.search_hosts(db_conn, ipv4_addr=ip_addr)
        if db_host is None:
            db.add_host(db_conn, ipv4_addr=ip_addr, mac_addr=mac_addr)
        else:
            db.set_host(db_conn, db_host.id, mac_addr=mac_addr)
    db_conn.close()

class Module:
    """Attempts to perform ARP lookups for all hosts in a given range to test which are live (also retrieves MAC addresses)
    """
    def run(self, range: str, timeout: float = 5.0, interface: Interface = get_default_interface()):
        if "/" in range:
            ip_addresses = cidr_range(range)
        elif "-" in range:
            ip_addresses = ip_range(range)
        db_conn = db.open()
        lookup_threads = []
        for ip_addr in ip_addresses:
            thread = threads.create_thread(_lookup_thread_func, (ip_addr, timeout, interface))
            lookup_threads.append(thread)
            thread.start()
        for thread in lookup_threads:
            thread.join()
        return True