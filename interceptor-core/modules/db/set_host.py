from interceptor.net.addresses import IPv4Address, MACAddress
import interceptor.db as db
import interceptor.io as io

class Module:
    """
    This module sets a parameter on a host in the database
    """
    def run(self, host_id: int, ipv4_addr: IPv4Address = None, ipv6_addr: str = None, mac_addr: MACAddress = None):
        db_conn = db.open()
        if db.get_host(db_conn, host_id):
            db.set_host(db_conn, host_id, str(ipv4_addr), str(ipv6_addr), str(mac_addr))
        else:
            io.write("No such host.")
            return False
        return True