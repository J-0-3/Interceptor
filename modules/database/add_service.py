"""This module adds a service to the Interceptor database"""
import interceptor.database as db
import interceptor.io as io
import interceptor.formatting as fmt

def run(host_id: int, port: int, transport_protocol: str, service: str) -> bool:
    conn = db.open()
    svc_id = db.add_service(conn, host_id, transport_protocol, port, service)
    io.write(fmt.info(f"Added service with id {svc_id}"))
    return True