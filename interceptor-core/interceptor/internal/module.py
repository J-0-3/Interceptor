import interceptor.io as io
import inspect
import importlib
from types import ModuleType, GenericAlias
from typing import Callable

def _import_module_by_name(name: str) -> ModuleType:
    name = f"modules.{name}"
    module: ModuleType = importlib.import_module(name)
    return module

def _type_to_str(t: type | GenericAlias):
    if isinstance(t, type):
        return t.__name__
    else:
        return f"{t.__name__}[{', '.join([_type_to_str(a) for a in t.__args__])}]"

class Module:
    def __init__(self, name: str):
        self._name: str = name
        self._module = _import_module_by_name(name).Module()
        self._info: str = self._module.__doc__
        self._run_func: Callable = self._module.run
        self._run_args: list[inspect.Parameter] = list(
            inspect.signature(self._run_func)
                .parameters
                .values()
            )
        self._set_args: dict[inspect.Parameter] = {}
        if 'stop' in dir(self._module):
            self._stop_func: Callable = self._module.stop
        else:
            self._stop_func: Callable = lambda: None
        self._running: bool = False

    @property
    def running(self) -> bool:
        return self._running
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def info(self) -> dict:
        return {
            "name": self._name,
            "description": self._info,
            "args": [
                {
                    "name": arg.name,
                    "type": _type_to_str(arg.annotation),
                    "required": arg.default == inspect.Parameter.empty,
                    "default": str(arg.default) if arg.default != inspect.Parameter.empty else 'None'
                } for arg in self._run_args
            ]
        }
        
    def run(self) -> bool:
        io.create()
        if any(filter(lambda arg: arg.default == inspect.Parameter.empty and arg not in self._set_args, self._run_args)):
            io.write("One or more required arguments is not set.")
            return False
        args = tuple(self._set_args[arg] if arg in self._set_args else arg.default for arg in self._run_args)
        self._running = True
        res: bool = self._run_func(*args)
        self._running = False
        return res 
    
    def stop(self):
        self._stop_func()

    def set(self, arg_name: str, value: str):
        arg_fltr = list(filter(lambda a: a.name == arg_name, self._run_args))
        if len(arg_fltr) == 0:
            raise ValueError(f"Argument {arg_name} does not exist.")
        arg: inspect.Parameter = arg_fltr[0]
        arg_type: type | GenericAlias = arg.annotation
        if type(arg_type) is GenericAlias:
            origin_type: type = arg_type.__origin__
            if origin_type in [list, tuple]:
                items = origin_type(map(lambda s: s.strip(), value.split(',')))
                item_type: type = arg_type.__args__[0]
                try:
                    value_casted = list(map(item_type, items))
                except TypeError:
                    raise TypeError(f"Value in list cannot be converted to type {item_type.__name__}")
            else:
                raise TypeError(f"Unsupported generic type {origin_type.__name__} in function signature")
        else:
            try:
                value_casted = arg_type(value)
            except TypeError:
                raise TypeError(f"Value {value} cannot be converted to type {arg_type.__name__}")
        self._set_args[arg] = value_casted
    
    def clear(self, arg_name: str):
        arg_fltr = list(filter(lambda a: a.name == arg_name, self._run_args))
        if len(arg_fltr) == 0:
            raise Exception(f"Argument {arg_name} does not exist.")
        arg: inspect.Parameter = arg_fltr[0]
        try:
            self._set_args.pop(arg)
        except KeyError:
            pass