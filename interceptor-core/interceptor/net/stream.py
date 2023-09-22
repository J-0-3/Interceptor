import socket
from typing import Callable
import interceptor.net.protocols.ethernet as eth
import interceptor.net.protocols.ip as ip
import interceptor.net.protocols.icmp as icmp
import interceptor.net.protocols.arp as arp
import interceptor.net.protocols.tcp as tcp
from interceptor.net.interfaces import Interface

_filters: dict[str, dict[int, Callable[[list], list]]] = {}

def _decode_packet(raw: bytes) -> list[eth.EthernetFrame |
                                       arp.ARPPacket |
                                       ip.IPv4Packet |
                                       icmp.ICMPPacket |
                                       tcp.TCPPacket]:
    layers = []
    layer_2 = eth.parse_raw_ethernet_header(raw)
    layers.append(layer_2)
    layer_3 = None
    if layer_2.proto == 0x0806:
        try:
            layer_3 = arp.parse_raw_arp_packet(layer_2.payload)
            layers.append(layer_3)
        except ValueError:
            pass
    elif layer_2.proto == 0x0800:
        try:
            layer_3 = ip.parse_raw_ip_packet(layer_2.payload)
            layers.append(layer_3)
        except ValueError:
            pass
    layer_4 = None
    if isinstance(layer_3, ip.IPv4Packet):
        if layer_3.proto == 1:
            try:
                layer_4 = icmp.parse_raw_icmp_packet(layer_3.payload)
                layers.append(layer_4)
            except ValueError:
                pass
        elif layer_3.proto == 6:
            try:
                layer_4 = tcp.parse_raw_tcp_packet(layer_3.payload)
                layers.append(layer_4)
            except ValueError:
                pass
    return layers

def _open_socket(interface: Interface):
    raw_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 3)
    raw_sock.bind((interface.name, 3))
    raw_sock.setblocking(False)
    _filters[interface] = {}
    return raw_sock

def _process_pkt(interface: Interface, pkt: bytes):
    layers = _decode_packet(pkt)
    for fltr in _filters[interface]:
        if not fltr(layers):
            return
    for i, l in enumerate(layers[1:][::-1]):
        layers[i - 1].payload = l.raw

def remove_filter(interface: Interface, filter_id: int):
    try:
        _filters[interface].pop(filter_id) 
    except KeyError:
        pass

def register_filter(interface: Interface, fltr: Callable[[list], bool]) -> int:
    if interface in _filters:
        next_id = max(_filters[interface].keys()) + 1
        _filters[interface][next_id] = fltr
        return next_id
    else:
        return None
