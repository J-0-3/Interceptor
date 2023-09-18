from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.addresses import IPv4Address
from interceptor.net.sockets.layer2 import l2_send, l2_recv
from interceptor.net.protocols.ethernet import EthernetFrame
from interceptor.net.protocols.ip import IPv4Packet, parse_raw_ip_packet
from interceptor.net.protocols.arp import resolve_ip_to_mac
from typing import Callable
import socket
import time

class HostUnresolvedException(Exception):
    def __init__(self, host: IPv4Address):
        super().__init__(f"Cannot resolve host {host.dotted}")
    
def l3_send(target: IPv4Address,
            protocol: int,
            payload: bytes,
            interface: Interface = None,
            sender: IPv4Address = None,
            arp_timeout_s: float = 1,
            sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    if sender is None:
        sender = interface.ipv4_addr
    ip_packet = IPv4Packet(target, protocol, payload, sender)
    target_mac = resolve_ip_to_mac(target, interface, timeout_s=arp_timeout_s)
    if target_mac is None:
        raise HostUnresolvedException(target)
    l2_send(target_mac, 0x0800, ip_packet.raw, interface, sock=sock)

def l3_recv(count: int = 1,
            filter_func: Callable[[bytes, EthernetFrame, IPv4Packet], bool] = lambda r, f, p: True, 
            interface: Interface = None,
            timeout_s: float = 5,
            sock: socket.socket = None) -> tuple[bytes, EthernetFrame, IPv4Address] | list[tuple[bytes, EthernetFrame, IPv4Address]] | None:
    if interface is None:
        interface = get_default_interface()
    packets = []
    start = time.perf_counter()
    while time.perf_counter() - start < timeout_s and len(packets) < count:
        raw_frame, frame = l2_recv(1, interface=interface, timeout_s=timeout_s, sock=sock)
        try:
            ip_packet = parse_raw_ip_packet(frame.payload)
        except:
            continue
        if filter_func(raw_frame, frame, ip_packet):
            packets.append((raw_frame, frame, ip_packet))
    if count == 1:
        if len(packets) > 0:
            return packets[0]
        return None
    return packets