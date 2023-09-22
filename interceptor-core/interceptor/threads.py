from typing import Callable, Iterable, Mapping, Any
import threading
import interceptor.io as io

def _create_io_and_run(func: Callable, 
                       args: Iterable | None,
                       kwargs: Mapping | None,
                       parent_id: int):
    io.add_thread(parent_id, threading.get_ident())
    if kwargs is None:
        kwargs = {}
    if args is None:
        args = ()
    func(*args, **kwargs)

def create_thread(target: Callable,
                  args: Iterable | None = None,
                  kwargs: Mapping[str, Any] | None = None,
                  daemon: bool | None = None) -> threading.Thread:
    thread = threading.Thread(target=_create_io_and_run, 
                              args=(target, args, kwargs, threading.get_ident()),
                              daemon = daemon)
    return thread
