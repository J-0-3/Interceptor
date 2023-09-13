"""Contains classes for using the Address Resolution Protocol"""
from interceptor.net.addresses import IPv4Address, MACAddress
import interceptor.net.interfaces as ifaces
from interceptor.net.packets import send_l3

class ARPPacket:
    def __init__(self, operation: int, 
                proto_target: IPv4Address | str | int | bytes | list[int] | list[bytes],
                hw_target: MACAddress | str | int | bytes | list[int] | list[bytes] = "00:00:00:00:00:00",
                proto_sender: IPv4Address | str | int | bytes | list[int] | list[bytes] = None,
                hw_sender: MACAddress | str | int | bytes | list[int] | list[bytes] = None):
        self._operation: int = operation
        if isinstance(proto_target, IPv4Address):
            self._proto_target: IPv4Address = proto_target
        else:
            self._proto_target: IPv4Address = IPv4Address(proto_target)
        if isinstance(hw_target, MACAddress):
            self._hw_target: MACAddress = hw_target
        else:
            self._hw_target: MACAddress = MACAddress(hw_target)
        if proto_sender is None:
            proto_sender: IPv4Address = ifaces.get_default_interface().ipv4_addr
        if hw_sender is None:
            hw_sender: MACAddress = ifaces.Interface(proto_sender).mac_addr
        if isinstance(proto_sender, IPv4Address):
            self._proto_sender: IPv4Address = proto_sender
        else:
            self._proto_sender: IPv4Address = IPv4Address(proto_sender)
        if isinstance(hw_sender, MACAddress):
            self._hw_sender: MACAddress = hw_sender
        else:
            self._hw_sender: MACAddress = MACAddress(hw_sender)
        self._hw_type: int = 1
        self._ptype: int = 0x0800

    @property
    def proto_target(self) -> IPv4Address:
        return self._proto_target
    
    @property
    def hw_target(self) -> MACAddress:
        return self._hw_target
    
    @property
    def proto_sender(self) -> IPv4Address:
        return self._proto_sender
    
    @property
    def hw_sender(self) -> MACAddress:
        return self._hw_sender
    
    @property
    def raw(self) -> bytes:
        pkt_bytes = self._hw_type.to_bytes(2, 'big')
        pkt_bytes += self._ptype.to_bytes(2, 'big')
        pkt_bytes += len(self._hw_target.octets).to_bytes(1, 'big')
        pkt_bytes += len(self._proto_target.octets).to_bytes(1, 'big')
        pkt_bytes += self._operation.to_bytes(2, 'big')
        pkt_bytes += self._hw_sender.bytestring
        pkt_bytes += self._proto_sender.bytestring
        pkt_bytes += self._hw_target.bytestring
        pkt_bytes += self._proto_target.bytestring
        return pkt_bytes
    
    def send(self, dst: MACAddress = "ff:ff:ff:ff:ff:ff", interface: ifaces.Interface = None) -> bool:
        if interface is None:
            try:
                interface = ifaces.Interface(self._hw_sender)
            except:
                interface = ifaces.get_default_interface()
        return send_l3(dst, self.raw, 0x0806, interface)
    
def parse_raw_arp_packet(data: bytes) -> ARPPacket:
    if len(data) < 28:
        raise ValueError("Invalid ARP Packet")
    operation = int.from_bytes(data[6:7], 'big')
    hw_sender = MACAddress(data[8:14])
    proto_sender = IPv4Address(data[14:18])
    hw_target = MACAddress(data[18:24])
    proto_target = IPv4Address(data[24:28])
    return ARPPacket(operation, proto_target, hw_target, proto_sender, hw_sender)