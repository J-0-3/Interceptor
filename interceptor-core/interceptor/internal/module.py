import interceptor.io as io
import inspect
import importlib
from types import ModuleType, GenericAlias, NoneType
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
        args = []
        for arg in self._run_args:
            if isinstance(arg.default, (str, int, NoneType, float, bool)):
                def_arg = arg.default
            elif arg.default == inspect.Parameter.empty:
                def_arg = None
            else:
                def_arg = str(arg.default)
            args.append({
                "name": arg.name,
                "type": _type_to_str(arg.annotation),
                "required": arg.default == inspect.Parameter.empty,
                "default": def_arg
            })
        return {
            "name": self._name,
            "description": self._info,
            "args": args
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
        if isinstance(arg_type, GenericAlias):
            origin_type: type = arg_type.__origin__
            if value == '':
                value_casted = None
            elif origin_type in [list, tuple]:
                items = origin_type(map(lambda s: s.strip(), value.split(',')))
                item_type: type = arg_type.__args__[0]
                try:
                    value_casted = list(map(item_type, items))
                except (TypeError, ValueError) as exc:
                    raise TypeError(f"Value in list cannot be converted to type {item_type.__name__}") from exc
            else:
                raise TypeError(f"Unsupported generic type {origin_type.__name__} in function signature")
        else:
            if value == '':
                value_casted = None
            try:
                if isinstance(arg_type, bool):
                    value_casted = value.lower() == "true"
                else:
                    value_casted = arg_type(value)
            except TypeError as exc:
                raise TypeError(f"Value {value} cannot be converted to type {arg_type.__name__}") from exc
        self._set_args[arg] = value_casted
    
    def clear(self, arg_name: str):
        arg_fltr = list(filter(lambda a: a.name == arg_name, self._run_args))
        if len(arg_fltr) == 0:
            raise ValueError(f"Argument {arg_name} does not exist.")
        arg: inspect.Parameter = arg_fltr[0]
        try:
            self._set_args.pop(arg)
        except KeyError:
            pass