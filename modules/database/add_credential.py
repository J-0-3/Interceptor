"""This module adds a credential to the Interceptor database"""
import interceptor.database as db
import interceptor.io as io
import interceptor.formatting as fmt

def run(service_id: int, login_name: str, credential: str) -> bool:
    conn = db.open()
    cred_id = db.add_credential(conn, service_id, login_name, credential)
    io.write(fmt.info(f"Added credential with id {cred_id}"))
    return True