from interceptor.net.sockets.layer1 import open_socket
from interceptor.net.sockets.layer2 import l2_recv
from interceptor.net.protocols.ip import parse_raw_ip_packet
from interceptor.net.interfaces import Interface, get_default_interface
import interceptor.io as io
import re

def _compile_filter(filter_str: str):
    if filter_str == "":
        return lambda ip, eth: True
    tokens = map(lambda t: t.strip(), filter_str.split())
    keywords = filter(lambda t: re.fullmatch(r'(([0-9]{1,3}\.){3}[0-9]{1,3})|(([0-9a-fA-F]{2}(:|-)){5}[0-9a-fA-F]{2})|(0x)?[0-9]+', t) == None, tokens)
    if any(filter(lambda k: k not in [
        'ip',
        'eth',
        'src',
        'dst',
        'proto',
        '=',
        'not',
        'and',
        'or'], keywords)):
        raise ValueError("Cannot parse")
    parsed: str = re.sub(r'(ip|eth) (src|dst|proto)', r'\1.\2', filter_str)
    parsed = re.sub(r'(([0-9]{1,3}\.){3}[0-9]{1,3})|(([0-9a-fA-F]{2}(:|-)){5}[0-9a-fA-F]{2})', r"'\1'", parsed)
    parsed = parsed.replace('=', '==')
    return lambda ip, eth: eval(parsed)

class Module:
    """Captures traffic on an interface and optionally write a hexdump to the output.
    """
    def run(self, interface: Interface = get_default_interface(), hexdump: int = 0, asciidump: int = 0, filter: str = ""):
        io.write("Opening socket.")
        sock = open_socket(interface)
        filter_func = _compile_filter(filter)
        while True:
            raw, frame = l2_recv(interface=interface, sock=sock)
            if "ip" in filter and frame.proto != 0x0800:
                continue
            if frame.proto == 0x0800:
                pkt = parse_raw_ip_packet(frame.payload)
            else:
                pkt = None
            if filter_func(pkt, frame):
                io.write(str(frame))
                if pkt is not None:
                    io.write(str(pkt))
                if hexdump:
                    io.write(frame.payload.hex())
                if asciidump:
                    io.write(''.join(chr(c) if c in range(32, 127) else '.' for c in frame.payload))