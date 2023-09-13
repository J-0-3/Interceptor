"""This module implements functions for sending and receiving packets at the link layer"""
from interceptor.net.addresses import MACAddress
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.net.protocols.ethernet as ether
import pylibpcap
import multiprocessing
import time

def send_l3(receiver: MACAddress, data: bytes, ethertype: int, interface: Interface = None):
    if interface is None:
        interface = get_default_interface()
    hdr = ether.EthernetHeader(ethertype, receiver, interface.mac_addr)
    return pylibpcap.send_packet(interface.name, hdr.raw + data)

def send_l2(data: bytes, interface: Interface = None):
    if interface is None:
        interface = get_default_interface()
    return pylibpcap.send_packet(interface.name, data)

def _recv_thread(interface: Interface, filter: str, count: int, pkt_queue: multiprocessing.Queue):
    for length, time, pkt_raw in pylibpcap.sniff(interface.name, filters=filter, count = count):
        pkt_queue.put(pkt_raw)

class _CapturedPacket:
    def __init__(self, hdr: ether.EthernetHeader, payload: bytes):
        self.header = hdr
        self.payload = payload

def recv_l3(count = 1, bpf_filter: str = None, interface: Interface = None, timeout_s = 0) -> list[_CapturedPacket]:
    if interface is None:
        interface = get_default_interface()
    frames = multiprocessing.Queue()
    start_time = time.perf_counter()
    listen_proc = multiprocessing.Process(target = _recv_thread, args=(interface, bpf_filter, count, frames))
    listen_proc.start()
    while listen_proc.is_alive():
        if time.perf_counter() - start_time > timeout_s:
            listen_proc.terminate()
    packets = []
    while not frames.empty():
        frame = frames.get()
        hdr = ether.parse_raw_ethernet_header(frame[:14])
        packets.append(_CapturedPacket(hdr, frame[14:]))
    return packets