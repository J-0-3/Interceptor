"""This module adds a host to the Interceptor database"""
import interceptor.database as db
import interceptor.io as io
import interceptor.formatting as fmt

def run(ipv4_addr: str, ipv6_addr: str = "", mac_addr: str = "") -> bool:
    conn = db.open()
    host_id = db.add_host(conn, ipv4_addr, ipv6_addr, mac_addr)
    io.write(fmt.info(f"Added host with id {host_id}"))
    return True