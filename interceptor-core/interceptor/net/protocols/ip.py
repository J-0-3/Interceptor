from interceptor.net.addresses import IPv4Address
from interceptor.net.interfaces import get_default_interface
import random

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

class IPv4Packet:
    def __init__(self,
                 dst: IPv4Address,
                 protocol: int,
                 payload: bytes,
                 src: IPv4Address = None,
                 dscp = 0,
                 ecn = 0,
                 ttl = 64,
                 identification = -1,
                 flags = 2,
                 frag_offset = 0):
        if src is None:
            src = get_default_interface().ipv4_addr
        self._src = src
        self._dst = dst
        self._protocol = protocol
        self._payload = payload
        self._dscp = dscp
        self._ecn = ecn
        self._ttl = ttl
        if identification == -1:
            self._identification = random.randrange(1, 0xffff)
        else:
            self._identification = identification
        self._flags = flags
        self._frag_offset = frag_offset
    
    @property
    def raw(self) -> bytes:
        raw_bytes = b'\x45'
        raw_bytes += ((self._dscp << 2) | self._ecn).to_bytes(1, 'big')
        raw_bytes += (len(self._payload) + 20).to_bytes(2, 'big')
        raw_bytes += self._identification.to_bytes(2, 'big')
        raw_bytes += ((self._flags << 14) | self._frag_offset).to_bytes(2, 'big')
        raw_bytes += self._ttl.to_bytes(1, 'big')
        raw_bytes += self._protocol.to_bytes(1, 'big')
        raw_bytes += b'\x00\x00'
        raw_bytes += self._src.bytestring
        raw_bytes += self._dst.bytestring
        checksum = _calculate_checksum(raw_bytes)
        raw_bytes = raw_bytes[:10] + checksum.to_bytes(2, 'big') + raw_bytes[12:]
        raw_bytes += self._payload
        return raw_bytes

    @property
    def src(self) -> IPv4Address:
        return self._src
    
    @property
    def dst(self) -> IPv4Address:
        return self._dst
    
    @property
    def proto(self) -> int:
        return self._protocol
    
    @property
    def dscp(self) -> int:
        return self._dscp
    
    @property
    def ecn(self) -> int:
        return self._ecn
    
    @property
    def ttl(self) -> int:
        return self._ttl
    
    @property
    def identification(self) -> int:
        return self._identification
    
    @property
    def flags(self) -> int:
        return self._flags
    
    @property
    def frag_offset(self) -> int:
        return self._frag_offset
    
    @property
    def payload(self) -> bytes:
        return self._payload

    def __str__(self) -> str:
        return f"{self.src} -> {self.dst} ({hex(self.proto)[2:]})"

def parse_raw_ip_packet(raw: bytes) -> IPv4Packet:
    dscp = raw[1] >> 2
    ecn = raw[1] % 4
    ident = int.from_bytes(raw[4:6], 'big')
    flags_frag_offset = int.from_bytes(raw[6:8], 'big')
    flags = flags_frag_offset >> 14
    frag_offset = flags_frag_offset & 0x1fff
    ttl = raw[8]
    protocol = raw[9]
    src = IPv4Address(raw[12:16])
    dst = IPv4Address(raw[16:20])
    payload = raw[20:]
    return IPv4Packet(dst, protocol, payload, src, dscp, ecn, ttl, ident, flags, frag_offset)
