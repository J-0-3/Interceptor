from interceptor.net.interfaces import Interface, get_default_interface
from typing import Callable
import socket
import time

_ETH_P_ALL = 3

def open_socket(interface: Interface) -> socket.socket:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, _ETH_P_ALL)
    s.bind((interface.name, _ETH_P_ALL))
    s.setblocking(False)
    return s

def l1_send(frame: bytes, interface: Interface = None, sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    needs_close = False
    if sock is None:
        needs_close = True
        sock = open_socket(interface)
    try:
        sock.sendall(frame)
    except socket.error:
        if needs_close:
            sock.close()
        return False
    if needs_close:
        sock.close()
    return True

def l1_recv(count = 1,
            filter_func: Callable[[bytes], bool] = lambda p: True,
            interface: Interface = None,
            timeout_s: float = 5.0,
            sock: socket.socket = None):
    if interface is None:
        interface = get_default_interface()
    needs_close = False
    if sock is None:
        sock = open_socket(interface)
        needs_close = True
    frames = []
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < timeout_s and len(frames) < count:
        try:
            raw = sock.recv(1518)
            if filter_func(raw):
                frames.append(raw)
        except socket.error as e:
            continue
    if needs_close:
        sock.close()
    if count == 1:
        if len(frames) > 0:
            return frames[0]
        return None
    return frames