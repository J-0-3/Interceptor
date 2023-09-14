"""This module performs an ARP lookup to retrieve the MAC address of a given host"""
from interceptor.net.addresses import IPv4Address
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.net.protocols.arp as arp 
import interceptor.database as db
import interceptor.io as io

def run(host_id: int, interface: Interface = get_default_interface()) -> bool:
    db_conn = db.open()
    host = db.get_host(db_conn, host_id)
    if host is None:
        io.write("No such host exists.")
        return False
    if host.ipv4 is None:
        io.write("Host exists but has no IPv4 address.")
        return False
    arp_req = arp.ARPPacket(1, host.ipv4)
    io.write("Sending ARP request...")
    try:
        resp = arp_req.send_and_recv(interface=interface)
    except:
        io.write("Error sending ARP request (are you root?)")
        return False
    if resp is None:
        io.write("No ARP response received.")
        return False
    io.write("Received ARP response.")
    result_mac = resp.hw_sender
    io.write(f"MAC Address: {result_mac}")
    db.set_host(db_conn, host.id, mac_addr=str(result_mac))
    return True