import interceptor.db as db
import interceptor.io as io

class Module:
    """
    This module adds a credential to the Interceptor database
    """
    def run(self, service_id: int, login_name: str, credential: str) -> bool:
        conn = db.open()
        cred_id = db.add_credential(conn, service_id, login_name, credential)
        io.write(f"Added credential with id {cred_id}")
        return True