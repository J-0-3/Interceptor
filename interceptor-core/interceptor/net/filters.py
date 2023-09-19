from interceptor.net.protocols.ethernet import EthernetFrame
from interceptor.net.protocols.ip import IPv4Packet, parse_raw_ip_packet
from interceptor.net.protocols.arp import ARPPacket, parse_raw_arp_packet
from interceptor.net.protocols.icmp import ICMPPacket, parse_raw_icmp_packet
from interceptor.net.protocols.tcp import TCPPacket, parse_raw_tcp_packet
from typing import Callable
import inspect
import re

def compile_filter(filter_str) -> Callable[[EthernetFrame], bool]:
    if filter_str == "":
        return lambda frame: True
    filter_str = filter_str.lower()
    tokens = map(lambda t: t.strip(), filter_str.split())
    keywords = filter(lambda t: re.fullmatch(r'(([0-9]{1,3}\.){3}[0-9]{1,3})|(([0-9a-fA-F]{2}(:|-)){5}[0-9a-fA-F]{2})|(0x)?[0-9]+', t) == None, tokens)
    # remove IP addresses, MAC addresses and base 10 or 16 integers before checking the whitelist
    if any(filter(lambda k: k not in [
        'ip',
        'eth',
        'arp',
        "icmp",
        "tcp",
        'src',
        'dst',
        'proto',
        '=',
        ">",
        "<",
        ">=",
        "<=",
        'not',
        'and',
        'or',
        "pdst",
        "psrc",
        "hwdst",
        "hwsrc",
        "opcode",
        "type",
        "code",
        "id",
        "seq",
        "ack",
        "urg",
        "psh",
        "rst",
        "syn",
        "ece",
        "cwr"], keywords)):
        raise ValueError(f"Illegal keyword.")
    parsed: str = re.sub(r'(ip|eth|arp|icmp|tcp) (src|dst|proto|pdst|psrc|hwdst|hwsrc|opcode|type|code|id|seq|ack|urg|psh|rst|syn|ece|cwr)', r'\1.\2', filter_str)
    for token in parsed.split():
        if '.' in token and ('eth' in token or 'arp' in token or 'icmp' in token or 'ip' in token):
            proto, prop = token.split('.')
            proto_class = None
            match proto:
                case 'eth':
                    proto_class = EthernetFrame
                case 'arp':
                    proto_class = ARPPacket
                case 'icmp':
                    proto_class = ICMPPacket
                case 'ip':
                    proto_class = IPv4Packet
                case 'tcp':
                    proto_class = TCPPacket
                case _:
                    raise ValueError(f"No such protocol {proto}")
            try:
                attr = inspect.getattr_static(proto_class, prop)
            except AttributeError:
                raise ValueError(f"Protocol '{proto}' has no such property '{prop}'")
            if not isinstance(attr, property):
                raise ValueError(f"Protocol '{proto}' has no such property '{prop}'")
                
    parsed = re.sub(r'(([0-9]{1,3}\.){3}[0-9]{1,3})|(([0-9a-fA-F]{2}(:|-)){5}[0-9a-fA-F]{2})', r"'\1'", parsed)
    parsed = parsed.replace('=', '==')
    parsed = parsed.replace(' true', " True")
    parsed = parsed.replace(' false', ' False')
    def fltr(eth: EthernetFrame) -> bool:
        if any(filter(lambda k:k in parsed, {"ip", "icmp", "tcp"})):
            if eth.proto == 0x0800:
                try:
                    ip = parse_raw_ip_packet(eth.payload)
                except:
                    return False
            else:
                return False
        elif "arp" in parsed:
            if eth.proto == 0x0806:
                try:
                    arp = parse_raw_arp_packet(eth.payload)
                except:
                    return False
            else:
                return False
        if "icmp" in parsed:
            if ip.proto == 1:
                try:
                    icmp = parse_raw_icmp_packet(ip.payload)
                except:
                    return False
            else:
                return False
        if "tcp" in parsed:
            if ip.proto == 6:
                try:
                    tcp = parse_raw_tcp_packet(ip.payload)
                except:
                    return False
            else:
                return False
        return eval(parsed)
    return fltr