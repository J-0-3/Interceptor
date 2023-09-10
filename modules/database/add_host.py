"""This module adds a host to the Interceptor database"""
import interceptor.database as db

def run(host_ipv4_addr: str, host_ipv6_addr: str = "", host_mac_addr: str = "") -> bool:
    conn = db.open()
    host_id = db.add_host(conn, host_ipv4_addr, host_ipv6_addr, host_mac_addr)
    print(f"Added host with id {host_id}")
    return True