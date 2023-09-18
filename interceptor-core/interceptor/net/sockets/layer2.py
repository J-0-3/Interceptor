from interceptor.net.addresses import MACAddress
from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.protocols.ethernet import EthernetFrame, parse_raw_ethernet_header
from interceptor.net.sockets.layer1 import l1_send, l1_recv
from typing import Callable
import socket
import time

def l2_send(target: MACAddress,
            ethertype: int,
            data: bytes,
            interface: Interface = None,
            sender: MACAddress = None,
            sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    if sender is None:
        sender = interface.mac_addr
    frame = EthernetFrame(ethertype, target, data, sender)
    l1_send(frame.raw, interface, sock)

def l2_recv(count: int = 1,
            filter_func: Callable[[bytes, EthernetFrame], bool] = lambda r, p: True,
            interface: Interface = None, 
            timeout_s: float = 5,
            sock: socket.socket = None) -> tuple[bytes, EthernetFrame] | list[tuple[bytes, EthernetFrame]] | None:
    frames = []
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < timeout_s and len(frames) < count:
        raw_frame = l1_recv(interface=interface, sock=sock, timeout_s=timeout_s)
        frame = parse_raw_ethernet_header(raw_frame)
        if filter_func(raw_frame, frame):
            frames.append((raw_frame, frame))
    if count == 1:
        if len(frames) > 0:
            return frames[0]
        return None
    return frames