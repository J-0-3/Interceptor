from interceptor.net.addresses import IPv4Address
from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer3 import l3_send, l3_recv
from interceptor.net.protocols.ip import IPv4Packet
from interceptor.net.interfaces import Interface, get_default_interface
from enum import Enum
from socket import IPPROTO_ICMP

def _calculate_checksum(data: bytes):
    if len(data) % 2 != 0:
        data += b'\x00'
    checksum = 0
    words = [data[i:i+2] for i in range(0, len(data), 2)]
    for word in words:
        checksum += int.from_bytes(word, 'big')
        while checksum >> 16 > 0:
            overflow = checksum >> 16
            checksum = (checksum & 0xffff) + overflow
    checksum ^= 0xffff
    return checksum

class ICMPType(Enum):
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 3
    REDIRECT_MESSAGE = 5
    ECHO_REQUEST = 8
    ROUTER_ADVERTISEMENT = 9
    ROUTER_SOLICITATION = 10,
    TIME_EXCEEDED = 11
    BAD_IP_HEADER = 12
    TIMESTAMP = 13
    TIMESTAMP_REPLY = 14

class ICMPPacket:
    def __init__(self, type: ICMPType | int, code: int, payload: bytes = b'', id: int = 0, seq: int = 1):
        if isinstance(type, ICMPType):
            self._type = type.value
        else:
            self._type = type
        self._code = code
        self._payload = payload
        self._id = id
        self._seq = seq

    @property
    def type(self) -> int:
        return self._type
    
    @property
    def code(self) -> int:
        return self._code
    
    @property
    def payload(self) -> bytes:
        return self._payload
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def seq(self) -> int:
        return self._seq
    
    @property
    def raw(self) -> bytes:
        raw_bytes = self._type.to_bytes(1, 'big')
        raw_bytes += self._code.to_bytes(1, 'big')
        raw_bytes += b'\x00\x00'
        if self._type in (ICMPType.ECHO_REQUEST, ICMPType.ECHO_REPLY):
            raw_bytes += self._id.to_bytes(2, 'big')
            raw_bytes += self._seq.to_bytes(2, 'big')
        raw_bytes += self._payload
        checksum = _calculate_checksum(raw_bytes).to_bytes(2, 'big')
        raw_bytes = raw_bytes[:2] + checksum + raw_bytes[4:]
        return raw_bytes
    
    def send(self,
             target: IPv4Address,
             interface: Interface = None,
             sender: IPv4Address = None):
        l3_send(target, IPPROTO_ICMP, self.raw, interface, sender)

    def send_and_recv(self,
                      target: IPv4Address,
                      interface: Interface = None,
                      timeout_s: float = 5.0):
        if interface is None:
            interface = get_default_interface()

        def pkt_filter(raw: bytes, frame, pkt: IPv4Packet) -> bool:
            if pkt.src != target:
                return False
            if pkt.proto != IPPROTO_ICMP:
                return False
            if pkt.dst != interface.ipv4_addr:
                return False
            try:
                icmp_pkt = parse_raw_icmp_packet(pkt.payload)
            except:
                return False
            if self.type == ICMPType.ECHO_REQUEST:
                if icmp_pkt.id != self.id:
                    return False
                if icmp_pkt.type != ICMPType.ECHO_REPLY:
                    return False
                if icmp_pkt.payload != self.payload:
                    return False
            elif self.type == ICMPType.TIMESTAMP:
                if icmp_pkt.type != ICMPType.TIMESTAMP_REPLY:
                    return False
            return True

        sock = open_socket(interface)
        l3_send(target, IPPROTO_ICMP, self.raw, interface, sock = sock, arp_timeout_s=timeout_s)
        res = l3_recv(filter_func=pkt_filter, interface=interface, timeout_s=timeout_s, sock=sock)
        if res is not None:
            res = parse_raw_icmp_packet(res[2].payload)
        return res
    
def parse_raw_icmp_packet(raw: bytes) -> ICMPPacket:
    if len(raw) < 4:
        raise ValueError("Cannot decode ICMP packet.")
    type: int = raw[0]
    code: int = raw[1]
    if type in (ICMPType.ECHO_REQUEST, ICMPType.ECHO_REPLY):
        if len(raw) < 8:
            raise ValueError("Cannot decode ICMP ECHO packet.")
        id: int = int.from_bytes(raw[4:6], 'big')
        seq: int = int.from_bytes(raw[6:8], 'big')
        payload: bytes = raw[8:]
    else:
        id: int = 0
        seq: int = 0
        payload: bytes = raw[4:]
    return ICMPPacket(type, code, payload, id, seq)
