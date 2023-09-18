import interceptor.io as io
import threading
from typing import Callable, Iterable, Mapping, Any

def _create_io_and_run(func: Callable, 
                       args: Iterable | None,
                       kwargs: Mapping | None,
                       parent_id: int):
    io.add_thread(parent_id, threading.get_ident())
    func(*args, **kwargs)

def create_thread(target: Callable,
                  args: Iterable = (),
                  kwargs: Mapping[str, Any] | None = {},
                  daemon: bool | None = None) -> threading.Thread:
    thread = threading.Thread(target=_create_io_and_run, 
                              args=(target, args, kwargs, threading.get_ident()),
                              daemon = daemon)
    return thread
