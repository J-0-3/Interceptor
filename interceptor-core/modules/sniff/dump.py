from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer2 import l2_recv
from interceptor.net.protocols.ip import parse_raw_ip_packet
from interceptor.net.protocols.tcp import parse_raw_tcp_packet
from interceptor.net.interfaces import Interface, get_default_interface
from interceptor.net.filters import compile_filter
import interceptor.io as io
import re

class Module:
    """Captures traffic on an interface and optionally write a hexdump to the output.
    """
    def __init__(self):
        self.running = True

    def run(self, interface: Interface = get_default_interface(), hexdump: int = 0, asciidump: int = 0, filter: str = ""):
        io.write("Opening socket.")
        sock = open_socket(interface)
        try:
            filter_func = compile_filter(filter)
        except ValueError as e:
            io.write(f"Failed to compile filter: {e}")
            return False
        self.running = True
        while self.running:
            raw, frame = l2_recv(interface=interface, sock=sock)
            if filter_func(frame):
                io.write(str(frame))
                if frame.proto == 0x800:
                    try:
                        pkt = parse_raw_ip_packet(frame.payload)
                        io.write(str(pkt))
                        if pkt.proto == 0x6:
                            tcp_pkt = parse_raw_tcp_packet(pkt.payload)
                            io.write(str(tcp_pkt))
                    except ValueError:
                        pass
                if hexdump:
                    io.write(frame.payload.hex())
                if asciidump:
                    io.write(''.join(chr(c) if c in range(32, 127) else '.' for c in frame.payload))
    
    def stop(self):
        self.running = False