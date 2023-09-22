"""Contains classes for using the Address Resolution Protocol"""
from interceptor.net.addresses import IPv4Address, MACAddress
from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.protocols.ethernet import EthernetFrame
from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer2 import l2_send, l2_recv
import interceptor.db as db

def get_arp_table() -> dict[IPv4Address, MACAddress]:
    with open("/proc/net/arp", 'r', encoding='utf-8') as file:
        entries = file.readlines()[1:]
        table = {}
        for line in entries:
            ip_addr, _, _, mac_addr, _, _ = line.split()
            table[IPv4Address(ip_addr)] = MACAddress(mac_addr)
    return table 

def resolve_ip_to_mac(ip_address: IPv4Address, interface: Interface = None, timeout_s: float = 5) -> MACAddress | None:
    db_conn = db.open()
    q_result = db.search_hosts(db_conn, ipv4_addr=ip_address)
    if q_result is not None and q_result.mac is not None:
        return q_result.mac
    arp_table = get_arp_table()
    if ip_address in arp_table:
        return arp_table[ip_address]
    arp_req = ARPPacket(1, ip_address)
    res = arp_req.send_and_recv(interface=interface, timeout_s=timeout_s)
    if res:
        if q_result is not None:
            db.set_host(db_conn, q_result.id, mac_addr=res.hwsrc)
        return res.hwsrc
    return None

class ARPPacket:
    def __init__(self, operation: int, 
                pdst: IPv4Address | str | int | bytes | list[int] | list[bytes],
                hwdst: MACAddress | str | int | bytes | list[int] | list[bytes] = "00:00:00:00:00:00",
                psrc: IPv4Address | str | int | bytes | list[int] | list[bytes] = None,
                hwsrc: MACAddress | str | int | bytes | list[int] | list[bytes] = None):
        self._operation: int = operation
        if isinstance(pdst, IPv4Address):
            self._pdst: IPv4Address = pdst
        else:
            self._pdst: IPv4Address = IPv4Address(pdst)
        if isinstance(hwdst, MACAddress):
            self._hwdst: MACAddress = hwdst
        else:
            self._hwdst: MACAddress = MACAddress(hwdst)
        if psrc is None:
            psrc: IPv4Address = get_default_interface().ipv4_addr
        if hwsrc is None:
            hwsrc: MACAddress = Interface(psrc).mac_addr
        if isinstance(psrc, IPv4Address):
            self._psrc: IPv4Address = psrc
        else:
            self._psrc: IPv4Address = IPv4Address(psrc)
        if isinstance(hwsrc, MACAddress):
            self._hwsrc: MACAddress = hwsrc
        else:
            self._hwsrc: MACAddress = MACAddress(hwsrc)
        self._hw_type: int = 1
        self._ptype: int = 0x0800

    @property
    def pdst(self) -> IPv4Address:
        return self._pdst
    
    @pdst.setter
    def pdst(self, pdst: IPv4Address):
        self._pdst = pdst

    @property
    def hwdst(self) -> MACAddress:
        return self._hwdst
    
    @hwdst.setter
    def hwdst(self, hwdst: MACAddress):
        self._hwdst = hwdst

    @property
    def psrc(self) -> IPv4Address:
        return self._psrc
    
    @psrc.setter
    def psrc(self, psrc: IPv4Address):
        self._psrc = psrc

    @property
    def hwsrc(self) -> MACAddress:
        return self._hwsrc
    
    @hwsrc.setter
    def hwsrc(self, hwsrc: MACAddress):
        self._hwsrc = hwsrc
    
    @property
    def opcode(self) -> int:
        return self._operation
    
    @opcode.setter
    def opcode(self, opcode: int):
        self._operation = opcode
    
    @property
    def raw(self) -> bytes:
        pkt_bytes = self._hw_type.to_bytes(2, 'big')
        pkt_bytes += self._ptype.to_bytes(2, 'big')
        pkt_bytes += len(self._hwdst.octets).to_bytes(1, 'big')
        pkt_bytes += len(self._psrc.octets).to_bytes(1, 'big')
        pkt_bytes += self._operation.to_bytes(2, 'big')
        pkt_bytes += self._hwsrc.bytestring
        pkt_bytes += self._psrc.bytestring
        pkt_bytes += self._hwdst.bytestring
        pkt_bytes += self._pdst.bytestring
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
            if arp_data.psrc != self.pdst:
                return False
            if arp_data.pdst != interface.ipv4_addr:
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
