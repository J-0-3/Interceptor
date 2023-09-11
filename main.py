from interceptor.module import Module
import interceptor.database as db
import os

ASCII_ART = """
.___        __               .__                              
|   | _____/  |_  ___________|  |   ____ ______   ___________ 
|   |/    \   __\/ __ \_  __ \  |  /  _ \\\\____ \_/ __ \_  __ \\
|   |   |  \  | \  ___/|  | \/  |_(  <_> )  |_> >  ___/|  | \/
|___|___|  /__|  \___  >__|  |____/\____/|   __/ \___  >__|   
         \/          \/                  |__|        \/       
"""

def main():
    print(ASCII_ART)
    setup_needed = not os.path.isfile("interceptor.db")
    db_conn = db.open()
    if setup_needed:
        db.setup(db_conn)
    current_module = None
    while True:
        inp = input(f"CMD ({current_module.name if current_module else 'None'})> ")
        cmd = inp.split(" ")[0]
        args = inp.split(" ")[1:]
        match cmd:
            case "info":
                if current_module:
                    print(current_module.info())
            case "load":
                current_module = Module(args[0])
            case "set":
                if current_module:
                    current_module.set(args[0], args[1])
            case "run":
                if current_module:
                    current_module.run()
            case "hosts":
                for host in db.get_all_hosts(db_conn):
                    print(host)
            case "host":
                host = db.get_host(db_conn, int(args[0]))
                print(host)
            case "credentials"|"creds":
                for cred in db.get_all_credentials(db_conn):
                    print(cred)
            case "credential"|"cred":
                cred = db.get_credential(db_conn, int(args[0]))
                print(cred)
            case "services":
                for serv in db.get_all_services(db_conn):
                    print(serv)
            case "service":
                serv = db.get_service(db_conn, int(args[0]))
                print(serv)
            case "quit"|"exit":
                exit()

if __name__ == "__main__":
    main()