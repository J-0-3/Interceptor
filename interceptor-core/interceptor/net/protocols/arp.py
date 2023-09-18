"""Contains classes for using the Address Resolution Protocol"""
from interceptor.net.addresses import IPv4Address, MACAddress
from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.protocols.ethernet import EthernetFrame
from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer2 import l2_send, l2_recv
import interceptor.db as db

def get_arp_table() -> dict[IPv4Address, MACAddress]:
    with open("/proc/net/arp", 'r') as file:
        entries = file.readlines()[1:]
        table = {}
        for line in entries:
            ip_addr, _, _, mac_addr, _, _ = line.split()
            table[IPv4Address(ip_addr)] = MACAddress(mac_addr)
    return table 

def resolve_ip_to_mac(ip_address: IPv4Address, interface: Interface = None) -> MACAddress | None:
    db_conn = db.open()
    q_results = db.search_hosts(db_conn, ipv4_addr=ip_address)
    if len(q_results) > 0 and q_results[0].mac is not None:
        return q_results[0].mac
    arp_table = get_arp_table()
    if ip_address in arp_table:
        return arp_table[ip_address]
    arp_req = ARPPacket(1, ip_address)
    res = arp_req.send_and_recv(interface=interface)
    if res:
        return res.hw_sender
    return None

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
            proto_sender: IPv4Address = get_default_interface().ipv4_addr
        if hw_sender is None:
            hw_sender: MACAddress = Interface(proto_sender).mac_addr
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
    
    def send(self,
             target: MACAddress | int | str | bytes | list[int] | list[bytes] = "ff:ff:ff:ff:ff:ff",
             interface: Interface = None,
             spoof_mac: MACAddress = None):
        l2_send(target, 0x0806, self.raw, interface, spoof_mac)

    def send_and_recv(self,
                      target: MACAddress | int | str | bytes | list[int] | list[bytes] = "ff:ff:ff:ff:ff:ff",
                      interface: Interface = None,
                      timeout_s: float = 5.0):
        
        def pkt_filter(raw: bytes, frame: EthernetFrame) -> bool:
            if frame.dst != interface.mac_addr:
                return False
            if frame.proto != 0x0806:
                return False
            try:
                arp_data = parse_raw_arp_packet(frame.payload)
            except ValueError:
                return False
            if arp_data.proto_sender != self.proto_target:
                return False
            if arp_data.proto_target != interface.ipv4_addr:
                return False
            return True
        
        sock = open_socket(interface)
        l2_send(target, 0x0806, self.raw, interface, sock=sock)
        res = l2_recv(filter_func=pkt_filter, interface=interface, timeout_s=timeout_s, sock=sock)
        if res is None:
            return None
        raw, frame = res
        return parse_raw_arp_packet(frame.payload)
    
def parse_raw_arp_packet(data: bytes) -> ARPPacket:
    if len(data) < 28:
        raise ValueError("Invalid ARP Packet")
    operation = int.from_bytes(data[6:7], 'big')
    hw_sender = MACAddress(data[8:14])
    proto_sender = IPv4Address(data[14:18])
    hw_target = MACAddress(data[18:24])
    proto_target = IPv4Address(data[24:28])
    return ARPPacket(operation, proto_target, hw_target, proto_sender, hw_sender)