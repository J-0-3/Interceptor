"""Contains classes for using the Ethernet protocol"""
from interceptor.net.addresses import MACAddress
from interceptor.net.interfaces import get_default_interface

class EthernetHeader:
    def __init__(self,proto: int, dst: MACAddress | str | int | bytes | list[int] | list[bytes], 
                 src: MACAddress | str | int | bytes | list[int] | list[bytes] = None):
        self._proto: int = proto
        self._dst: MACAddress = dst if isinstance(dst, MACAddress) else MACAddress(dst)
        if src is None:
            self._src: MACAddress = get_default_interface().mac_addr
        else:
            self._src: MACAddress = src if isinstance(src, MACAddress) else MACAddress(src)
    
    @property
    def raw(self) -> bytes:
        return self._dst.bytestring + self._src.bytestring + self._proto.to_bytes(2, 'big')

    @property
    def dst(self) -> MACAddress:
        return self._dst
    
    @property
    def src(self) -> MACAddress:
        return self._src
    
    @property
    def proto(self) -> int:
        return self._proto
    
    def __str__(self) -> str:
        return f"{self.src} -> {self.dst} ({hex(self.proto)[2:]})"
    
def parse_raw_ethernet_header(raw_hdr: bytes) -> EthernetHeader:
    dst = MACAddress(raw_hdr[:6])
    src = MACAddress(raw_hdr[6:12])
    ethertype = int.from_bytes(raw_hdr[12:14], 'big')
    return EthernetHeader(ethertype, dst, src)