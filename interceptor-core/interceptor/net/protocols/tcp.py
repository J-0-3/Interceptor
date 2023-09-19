import random
import socket

class TCPPacket:
    def __init__(self, dst: int,
                 payload: bytes,
                 src: int = -1,
                 seq: int = 0,
                 ack_num: int = 0,
                 flags: int = 0,
                 window_size: int = 65535,
                 urg_ptr: int = 0,
                 options: dict[int, bytes] = []):
        self._dst = dst
        self._payload = payload
        if src == -1:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', 0))
            _, self._src = s.getsockname()
            s.close()
        else:
            self._src = src
        if seq == 0:
            self._seq = random.randrange(0, 2**32)
        else:
            self._seq = seq
        self._ack_num = ack_num
        self._flags = flags
        self._window_size = window_size
        self._urg_ptr = urg_ptr
        self._options = options

    @property
    def dst(self) -> int:
        return self._dst

    @property
    def src(self) -> int:
        return self._src

    @property
    def payload(self) -> bytes:
        return self._payload

    @property
    def seq(self) -> int:
        return self._seq

    @property
    def ack_num(self) -> int:
        return self._ack_num

    @property
    def flags(self) -> int:
        return self._flags

    @property
    def window_size(self) -> int:
        return self._window_size

    @property
    def urg_ptr(self) -> int:
        return self._urg_ptr

    @property
    def options(self) -> dict[int, bytes]:
        return self._options

    @property
    def fin(self) -> bool:
        return bool(self._flags & 1)

    @property
    def syn(self) -> bool:
        return bool(self._flags & 2)

    @property
    def rst(self) -> bool:
        return bool(self._flags & 4)
    
    @property
    def psh(self) -> bool:
        return bool(self._flags & 8)
    
    @property
    def ack(self) -> bool:
        return bool(self._flags & 0x10)
    
    @property
    def urg(self) -> bool:
        return bool(self._flags & 0x20)
    
    @property
    def ece(self) -> bool:
        return bool(self._flags & 0x40)

    @property
    def cwr(self) -> bool:
        return bool(self._flags & 0x80)

    def __str__(self) -> str:
        s = f"{self._src} -> {self._dst}"
        c_bit = 1
        for flag in ("FIN", "SYN", "RST", "PSH", "ACK", "URG", "ECE", "CWR"):
            if (self._flags & c_bit) != 0:
                s += f" {flag}"
            c_bit <<= 1
        return s
    
def parse_raw_tcp_packet(raw: bytes):
    src = int.from_bytes(raw[:2], 'big')
    dst = int.from_bytes(raw[2:4], 'big')
    seq_num = int.from_bytes(raw[4:8], 'big')
    ack_num = int.from_bytes(raw[8:12], 'big')
    header_len = (raw[12] >> 4) * 4
    flags = raw[13]
    win_size = int.from_bytes(raw[14:16], 'big')
    urg_ptr = int.from_bytes(raw[18:20], 'big')
    opts_raw = raw[20:header_len]
    options = {}
    index = 0
    while index < len(opts_raw):
        opt_kind = opts_raw[index]
        if opt_kind == 0:
            break
        elif opt_kind == 1:
            index += 1
            continue
        if index + 1 < len(opts_raw):
            opt_len = opts_raw[index + 1]
        else:
            raise ValueError("Options field malformed")
        if index + opt_len <= len(opts_raw):
            opt_data = opts_raw[index + 2:index + opt_len]
        else:
            raise ValueError("Options field incorrect length")
        options[opt_kind] = opt_data
        index += opt_len
    payload = raw[header_len:]
    return TCPPacket(dst, payload, src, seq_num, ack_num, flags, win_size, urg_ptr, options)