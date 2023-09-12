"""This module counts up to 30 over 30 seconds, for testing Interceptor background tasks"""
import interceptor.io as io
import interceptor.formatting as fmt
from time import sleep

def run():
    for i in range(1, 31):
        io.write(i)
        sleep(1)
    io.write(fmt.success("Finished counting to 30!"))