from functools import reduce

class IPv4Address:
    """
    Represents an Internet Protocol version 4 address.
    """
    def __init__(self, addr: str | int | bytes | list[int] | list[bytes]):
        """
        Constructs an IPv4Address.

        Args:
            addr (str | int | bytes | list[int] | list[bytes]): The address in dotted (a.b.c.d), integer, bytestring, or octet list form.
        """
        if isinstance(addr, str):
            self._octets: list[int] = list(map(lambda o: int(o), addr.split('.')))
        elif isinstance(addr, int):
            self._octets: list[int] = [(addr & (0xff << s)) >> s for s in range(0, 32, 8)][::-1]
        elif isinstance(addr, bytes):
            self._octets: list[int] = list(addr)
        elif isinstance(addr, list) and all(map(lambda x: isinstance(x, int), addr)):
            self._octets: list[int] = list(addr)
        elif isinstance(addr, list) and all(map(lambda x: isinstance(x, bytes), addr)):
            self._octets: list[int] = list(map(int, addr))
        else:
            raise Exception("Required argument not set")
        
    @property
    def dotted(self) -> str:
        """
        The dotted (a.b.c.d) representation of the address. 
        """
        return '.'.join(map(str, self._octets))
    
    @property
    def i32(self) -> int:
        """
        The 32-bit integer representation of the address.
        """
        return reduce(lambda x, y: x << 8 | y, self._octets)

    @property
    def bytestring(self) -> bytes:
        """
        The address as a string of 4 bytes.
        """
        return b''.join(map(lambda i: i.to_bytes(1), self._octets))

    @property
    def octets(self) -> list[int]:
        """
        The individual 8 bit integer octets in the address.
        """
        return self._octets

    @property
    def ip_class(self) -> str:
        """
        The addressing class (A-E) which the address belongs to.
        """
        if self >= "1.0.0.0" and self <= "127.255.255.255":
            return "A"
        elif self >= "128.0.0.0" and self <= "191.255.255.255":
            return "B"
        elif self >= "192.0.0.0" and self <= "223.255.255.255":
            return "C"
        elif self >= "224.0.0.0" and self <= "239.255.255.255":
            return "D"
        else:
            return "E"
    
    @property
    def private(self) -> bool:
        """
        Whether the IP address is within a private IP range.
        """
        return any(lambda r: self >= r[0] and self <= r[1] for r in [
            ("10.0.0.0", "10.255.255.255"),
            ("172.16.0.0", "172.31.255.255"),
            ("192.168.0.0", "192.168.255.255")
        ])
    
    @property
    def loopback(self) -> bool:
        """
        Whether the IP address falls within the loopback range (127.0.0.1/8).
        """
        return self >= "127.0.0.1" and self <= "127.255.255.255"
    
    @property
    def public(self) -> bool:
        """
        Whether the IP address falls within a public IP range.
        """
        return not self.private
    
    @property
    def multicast(self) -> bool:
        """
        Whether the IP address is in the multicast range (class D).
        """
        return self.ip_class == "D"
    
    @property
    def research(self) -> bool:
        """
        Whether the IP address is in the research range (class E).
        """
        return self.ip_class == "E"


    def __str__(self) -> str:
        return self.dotted
    
    def __int__(self) -> int:
        return self.i32
    
    def __bytes__(self) -> bytes:
        return self.bytestring
    
    def __iter__(self) -> list[int]:
        return self._octets
    
    def __and__(self, other):
        if isinstance(other, IPv4Address):
            other_int = other.i32
        else:
            other_int = IPv4Address(other).i32
        return IPv4Address(self.i32 & other_int)
    
    def __invert__(self):
        return IPv4Address(~self.i32)
    
    def __or__(self, other):
        if isinstance(other, IPv4Address):
            other_int = other.i32
        else:
            other_int = IPv4Address(other).i32
        return IPv4Address(self.i32 | other_int)
    
    def __xor__(self, other):
        if isinstance(other, IPv4Address):
            other_int = other.i32
        else:
            other_int = IPv4Address(other).i32
        return IPv4Address(self.i32 ^ other_int)
    
    def __eq__(self, other):
        if isinstance(other, IPv4Address):
            return self._octets == other.octets
        else:
            return self._octets == IPv4Address(other).octets

    def __gt__(self, other):
        if isinstance(other, IPv4Address):
            return self.i32 == other.i32
        else:
            return self.i32 > IPv4Address(other).i32

    def __lt__(self, other):
        if isinstance(other, IPv4Address):
            return self.i32 < other.i32
        else:
            return self.i32 < IPv4Address(other).i32
    
    def __ge__(self, other):
        if isinstance(other, IPv4Address):
            return self.i32 >= other.i32
        else:
            return self.i32 >= IPv4Address(other).i32
        
    def __le__(self, other):
        if isinstance(other, IPv4Address):
            return self.i32 <= other.i32
        else:
            return self.i32 <= IPv4Address(other).i32

def cidr_range(cidr: str) -> list[IPv4Address]:
    """
    Gets all the IP addresses within a CIDR range ("a.b.c.d/n")
    
    Args:
        cidr (str): The range in CIDR notation (<address>/<mask bits>)
    """
    addr, bits = cidr.split("/")
    addr = IPv4Address(addr)
    bits = int(bits)
    subnet_mask = IPv4Address(reduce(lambda x, y: x | y, (2**(32 - 1) >> i for i in range(bits))))
    subnet_id = addr & subnet_mask
    brdcast_ip = addr | ~subnet_mask
    return [IPv4Address(a) for a in range(subnet_id.i32 + 1, brdcast_ip.i32)]

class MACAddress:
    """
    Represents a Media Access Control address.
    """
    def __init__(self, addr: str | int | bytes | list[int] | list[bytes]):
        """
        Construct a MACAddress object. 
        
        Args:
            addr (str | int | bytes | list[int] | list[bytes]): The address in 
            hexadecimal colon or hyphen, integer, bytestring, or octet list form.
        """
        if isinstance(addr, str):
            if ':' in addr:
                self._octets: list[int] = list(map(lambda i: int(i, 16), addr.split(':')))
            elif '-' in addr:
                self._octets: list[int] = list(map(lambda i: int(i, 16), addr.split('-')))
        elif isinstance(addr, int):
            self._octets: list[int] = [(addr & (0xff << s)) >> s for s in range(0, 48, 8)]
        elif isinstance(addr, bytes):
            self._octets: list[int] = list(addr)
        elif isinstance(addr, list) and all(map(lambda x: isinstance(x, int), addr)):
            self._octets: list[int] = addr
        elif isinstance(addr, bytes) and all(map(lambda x: isinstance(x, bytes), addr)):
            self._octets: list[int] = list(map(int, addr))
        else:
            raise Exception("Cannot convert type to MAC address")
    
    @property
    def colon(self) -> str:
        """
        The MAC address in colon-separated hexadecimal form (12:34:56:ab:cd:ef)
        """
        return ':'.join(map(lambda i: hex(i)[2:].zfill(2), self._octets))

    @property
    def hyphen(self) -> str:
        """
        The MAC address in hyphen-separated hexadecimal form (12-34-56-ab-cd-ef)
        """
        return '-'.join(map(lambda i: hex(i)[2:].zfill(2), self._octets))
    
    @property
    def i48(self) -> int:
        """
        The MAC address as a 48-bit integer.
        """
        return reduce(lambda x, y: x << 8 | y, self._octets)

    @property
    def bytestring(self) -> bytes:
        """
        The MAC address as a string of individual bytes
        """
        return b''.join(map(lambda i: i.to_bytes(1), self._octets))
    
    @property
    def octets(self) -> list[int]:
        """
        The 6 individual 8-bit integer octets that make up the MAC address.
        """
        return self._octets
    
    @property
    def universal(self) -> bool:
        """
        Whether the MAC address is universally administered (equivalent to not local).
        """
        return not bool(self._octets[0] & 2)
    
    @property
    def local(self) -> bool:
        """
        Whether the MAC address is locally administered (equivalent to not universal).
        """
        return bool(self._octets[0] & 2)
    
    @property
    def unicast(self) -> bool:
        """
        Whether the MAC address is a unicast address (equivalent to not multicast).
        """
        return not bool(self._octets[0] & 1)
    
    @property
    def multicast(self) -> bool:
        """
        Whether the MAC address is a multicast address (equivalent to not unicast).
        """
        return bool(self._octets[0] & 1)
    
    @property
    def oui(self) -> str:
        """
        The Organizationally Unique Identifier in hexadecimal-colon form (ab:cd:ef)
        """
        return self.colon[:8]

    @property
    def nic(self) -> str:
        """
        The Network Interface Card identifier in hexadecimal-colon form (ab:cd:ef)
        """
        return self.colon[9:]
    
    def __str__(self) -> str:
        return self.colon

    def __int__(self) -> int:
        return self.i48
    
    def __bytes__(self) -> bytes:
        return self.bytestring
    
    def __iter__(self) -> list[int]:
        return self._octets
    
    def __and__(self, other):
        if isinstance(other, MACAddress):
            other_int = other.i48
        else:
            other_int = MACAddress(other).i48
        return MACAddress(self.i48 & other_int)
    
    def __or__(self, other):
        if isinstance(other, MACAddress):
            other_int = other.i48
        else:
            other_int = MACAddress(other).i48
        return MACAddress(self.i48 | other_int)
    
    def __xor__(self, other):
        if isinstance(other, MACAddress):
            other_int = other.i48
        else:
            other_int = MACAddress(other).i48
        return MACAddress(self.i48 ^ other_int)
    
    def __invert__(self):
        return MACAddress(~self.i48)