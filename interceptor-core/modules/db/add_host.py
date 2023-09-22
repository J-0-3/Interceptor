from interceptor.net.addresses import IPv4Address, MACAddress
from interceptor import db
from interceptor import io

class Module:
    """This module adds a host to the Interceptor database
    """
    def run(self, ipv4_addr: IPv4Address = None, ipv6_addr: str = None, mac_addr: MACAddress = None) -> bool:
        conn = db.open()
        host_id = db.add_host(conn, ipv4_addr, ipv6_addr, mac_addr)
        io.write(f"Added host with id {host_id}")
        return True