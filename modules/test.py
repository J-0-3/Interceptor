"""This module is a mock module for testing the Interceptor module loading system """
import interceptor.io as io

def run(arg_1: int, arg_2: str, arg_3: float) -> bool:
    io.write(arg_1)
    io.write(arg_2)
    io.write(arg_3)
    return True