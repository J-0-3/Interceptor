import inspect
from queue import Queue

_IO_QUEUES: dict[str, Queue] = {}

def create(module_name: str):
    _IO_QUEUES[module_name] = Queue()

def write(text: str):
    calling_module = inspect.currentframe().f_back.f_globals['__name__'].split('.', 1)[1]
    _IO_QUEUES[calling_module].put(text)

def available(module: str) -> bool:
    if module not in _IO_QUEUES:
        return False
    return not _IO_QUEUES[module].empty()

def read(module: str) -> str:
    return _IO_QUEUES[module].get()