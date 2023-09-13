"""This module performs an ARP lookup to retrieve the MAC address of a given host"""
from interceptor.net.addresses import IPv4Address
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.net.protocols.arp as arp 
from interceptor.net.packets import recv_l3
import interceptor.database as db
import interceptor.io as io
import interceptor.formatting as fmt

def run(target_ip: IPv4Address, interface: Interface = get_default_interface()) -> bool:
    db_conn = db.open()
    search_res = db.search_hosts(db_conn, ipv4_addr=target_ip.dotted)
    if len(search_res) > 0:
        host_id = search_res[0].id
    else:
        host_id = db.add_host(db_conn, target_ip.dotted)
    io.write(fmt.info("Sending ARP request..."))
    arp_pkt = arp.ARPPacket(1, target_ip)
    if (arp_pkt.send(interface=interface)):
        io.write(fmt.success("ARP request sent successfully."))
    else:
        io.write(fmt.error("Could not send ARP request (are you root?)"))
        return False
    io.write(fmt.info("Waiting for ARP response..."))
    pkts = recv_l3(1, f"arp and dst host {str(interface.ipv4_addr)} and src host {str(target_ip)}", interface, 5)
    if len(pkts) == 0:
        io.write(fmt.error("No ARP response received from target."))
        return False
    io.write(fmt.success("Received ARP response."))
    arp_resp = arp.parse_raw_arp_packet(pkts[0].payload)
    result_mac = arp_resp.hw_sender
    io.write(fmt.info(f"MAC Address: {result_mac}"))
    db.set_host(db_conn, host_id, mac_addr=str(result_mac))
    return True