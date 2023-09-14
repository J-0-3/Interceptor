"""This module adds a host to the Interceptor database"""
import interceptor.database as db
import interceptor.io as io

def run(ipv4_addr: str = None, ipv6_addr: str = None, mac_addr: str = None) -> bool:
    conn = db.open()
    host_id = db.add_host(conn, ipv4_addr, ipv6_addr, mac_addr)
    io.write(f"Added host with id {host_id}")
    return True