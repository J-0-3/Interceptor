import threading
from queue import Queue

_IO_QUEUES: dict[str, Queue[str]] = {}

def create():
    _IO_QUEUES[threading.get_ident()] = Queue()

def write(text: str):
    thread_id = threading.get_ident()
    _IO_QUEUES[thread_id].put(text)

def available(thread_id: int) -> bool:
    if thread_id not in _IO_QUEUES:
        return False
    return not _IO_QUEUES[thread_id].empty()

def read(thread_id: int) -> str:
    return _IO_QUEUES[thread_id].get()

def add_thread(parent_thread_id: int, child_thread_id: int):
    _IO_QUEUES[child_thread_id] = _IO_QUEUES[parent_thread_id]