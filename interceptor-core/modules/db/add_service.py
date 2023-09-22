from interceptor import db
from interceptor import io

class Module:
    """This module adds a service to the Interceptor database
    """
    def run(self, host_id: int, port: int, transport_protocol: str) -> bool:
        conn = db.open()
        svc_id = db.add_service(conn, host_id, transport_protocol, port)
        io.write(f"Added service with id {svc_id}")
        return True