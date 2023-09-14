"""This module implements functions for sending and receiving packets at the link layer"""
from interceptor.net.addresses import MACAddress
from interceptor.net.interfaces import Interface, get_default_interface
from typing import Callable
from threading import Thread
from queue import Queue
import interceptor.net.protocols.ethernet as ether
import socket
import time

_ETH_P_ALL = 3

def _open_raw_socket(interface: Interface) -> socket.socket:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, _ETH_P_ALL)
    s.bind((interface.name, _ETH_P_ALL))
    s.setblocking(False)
    return s

def send_l3(receiver: MACAddress | str | bytes | int | list[int] | list[bytes],
            data: bytes,
            ethertype: int,
            interface: Interface = None,
            sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    hdr = ether.EthernetHeader(ethertype, receiver, interface.mac_addr)
    needs_close = False
    if sock is None:
        sock = _open_raw_socket(interface)
        needs_close = True
    try:
        sock.sendall(hdr.raw + data)
    except socket.error:
        if needs_close:
            sock.close()
        return False
    if needs_close:
        sock.close()
    return True


def send_l2(data: bytes, interface: Interface = None, sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    needs_close = False
    if sock is None:
        needs_close = True
        sock = _open_raw_socket(interface)
    try:
        sock.sendall(data)
    except socket.error:
        if needs_close:
            sock.close()
        return False
    if needs_close:
        sock.close()
    return True


class _CapturedPacket:
    def __init__(self, hdr: ether.EthernetHeader, payload: bytes):
        self.header = hdr
        self.payload = payload

def recv_l3(count = 1, filter_func: Callable[[_CapturedPacket], bool] = None, interface: Interface = None, timeout_s = 0, sock: socket.socket = None) -> list[_CapturedPacket]:
    if interface is None:
        interface = get_default_interface()
    pkts = []
    needs_close = False
    if sock is None:
        needs_close = True
        sock = _open_raw_socket(interface)
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < timeout_s and len(pkts) < count:
        try:
            raw_pkt = sock.recv(2048)
            hdr = ether.parse_raw_ethernet_header(raw_pkt[:14])
            data = raw_pkt[14:]
            pkt = _CapturedPacket(hdr, data)
            print(pkt.header)
            if filter_func(pkt):
                pkts.append(pkt)
        except socket.error as e:
            continue
    if needs_close:
        sock.close()
    return pkts

def send_and_recv_l3(target: MACAddress | str | bytes | int | list[int] | list[bytes],
                     data: bytes,
                     proto: int,
                     response_filter: Callable[[_CapturedPacket], bool] = None,
                     interface: Interface = None,
                     resp_count: int = 1,
                     timeout_s: int = 5):
    s = _open_raw_socket(interface)
    send_l3(target, data, proto, interface, s)
    pkts = recv_l3(resp_count, response_filter, interface, timeout_s, s)
    if resp_count == 1:
        if len(pkts) > 0:
            return pkts[0]
        return None
    return pkts