import sqlite3

def open() -> sqlite3.Connection:
    return sqlite3.connect("interceptor.db")

def setup(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("CREATE TABLE hosts (id INTEGER NOT NULL PRIMARY KEY , ipv4 TEXT, ipv6 TEXT, mac TEXT)")
    cur.execute("CREATE TABLE services (id INTEGER NOT NULL PRIMARY KEY, host_id INT, transport_protocol TEXT, port INT, service TEXT)")
    cur.execute("CREATE TABLE credentials (id INTEGER NOT NULL PRIMARY KEY, service_id INT, login_name TEXT, credential TEXT)")
    conn.commit()

def add_host(conn: sqlite3.Connection, ipv4_addr: str, ipv6_addr: str, mac_addr: str):
    cur = conn.cursor()
    cur.execute("INSERT INTO hosts (ipv4, ipv6, mac) VALUES (?, ?, ?)", (ipv4_addr, ipv6_addr, mac_addr))
    conn.commit()
    return cur.lastrowid

def add_service(conn: sqlite3.Connection, host_id: int, transport_protocol: str, port: int, service: str):
    cur = conn.cursor()
    cur.execute("INSERT INTO services (host_id, transport_protocol, port, service) VALUES (?, ?, ?, ?)", (host_id, transport_protocol, port, service))
    conn.commit()
    return cur.lastrowid

def add_credential(conn: sqlite3.Connection, service_id: int, login_name: str, credential: str):
    cur = conn.cursor()
    cur.execute("INSERT INTO credentials (service_id, login_name, credential) VALUES (?, ?, ?)", (service_id, login_name, credential))
    conn.commit()
    return cur.lastrowid

class _Host:
    def __init__(self, id, ipv4, ipv6, mac):
        self.id = id
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.mac = mac
    def __str__(self) -> str:
        return f"ID: {self.id}\n\tIPv4: {self.ipv4}\n\tIPv6: {self.ipv6}\n\tMAC: {self.mac}"

def get_all_hosts(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT * FROM hosts")
    res = cur.fetchall()
    return [_Host(*r) for r in res]

def get_host(conn:sqlite3.Connection, id: int):
    cur = conn.cursor()
    cur.execute("SELECT ipv4, ipv6, mac FROM hosts WHERE id = ?", (id,))
    res = cur.fetchone()
    if res is None:
        return None
    return _Host(id, *res)

class _Credential:
    def __init__(self, id: int, service_id: int, login_name: str, credential: str):
        self.id = id
        self.service_id = service_id
        self.login_name = login_name
        self.credential = credential
    def __str__(self) -> str:
        return f"ID: {self.id}\n\tService ID: {self.service_id}\n\tLogin Name: {self.login_name}\n\tCredential: {self.credential}"
    
def get_all_credentials(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT * FROM credentials")
    res = cur.fetchall()
    return [_Credential(*r) for r in res]

def get_credential(conn: sqlite3.Connection, id: int):
    cur = conn.cursor()
    cur.execute("SELECT service_id, login_name, credential FROM credentials WHERE id = ?", (id, ))
    res = cur.fetchone()
    if res is None:
        return None
    return _Credential(id, *res)

class _Service:
    def __init__(self, id: int, host_id: int, transport_protocol: str, port: int, service: str):
        self.id = id
        self.host_id = host_id
        self.transport_protocol = transport_protocol
        self.port = port
        self.service = service
    def __str__(self) -> str:
        return f"ID: {self.id}\n\tHost ID: {self.host_id}\n\tTransport Protocol: {self.transport_protocol}\n\tPort: {self.port}\n\tService: {self.service}"

def get_all_services(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT * FROM services")
    res = cur.fetchall()
    return [_Service(*r) for r in res]

def get_service(conn: sqlite3.Connection, id: int):
    cur = conn.cursor()
    cur.execute("SELECT host_id, transport_protocol, port, service FROM services WHERE id = ?", (id, ))
    res = cur.fetchone()
    if res is None:
        return None
    return _Service(id, *res)