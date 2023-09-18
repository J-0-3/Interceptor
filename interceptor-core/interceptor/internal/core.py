from interceptor.internal.module import Module
from threading import Thread
import interceptor.net.interfaces as ifaces
import interceptor.db as db
import interceptor.io as io
import os

class CoreApplication:
    def __init__(self):
        self._tasks: dict[str, Thread] = {}
        self._init_db()

    def _init_db(self):
        if not os.path.isfile("interceptor.db"):
            with db.open() as db_conn:    
                db.setup(db_conn)

    def get_module_info(self, module_name: str) -> dict:
        module = Module(module_name)
        return module.info
        
    def list_modules(self, category: str = "") -> list[str]:
        cur_root = f"modules/{category.replace('.', '/')}"
        dir_list = os.listdir(cur_root)
        mod_list = list (
            map(
                lambda filename: f"{category}{'.' if category else ''}{filename[:-3]}",
                filter(lambda f: os.path.isfile(f"{cur_root}/{f}") and f.endswith(".py"), dir_list)
            )
        )
        for dir in filter(lambda f: os.path.isdir(f"{cur_root}/{f}"), dir_list):
            mod_list += self.list_modules(f"{category}{'.' if category else ''}{dir}")
        return mod_list
    
    def start_module(self, module_name: str, module_args: dict) -> str:
        module = Module(module_name)
        for name, value in module_args.items():
            module.set(name, value)
        task_thread = Thread(target=module.run)
        task_thread.start()
        task_name = module_name
        suffix = 1
        while task_name in self._tasks:
            task_name = f"{task_name}_{suffix}"
            suffix += 1
        self._tasks[task_name] = (task_thread, module)
        return task_name
        
    def get_tasks(self):
        return list(self._tasks.keys())
    
    def get_task_status(self, task_name: str) -> dict:
        if task_name in self._tasks:
            thread = self._tasks[task_name][0]
            output = ""
            while io.available(thread.ident):
                output += f"{io.read(thread.ident)}\n"
            if not thread.is_alive():
                self._tasks.pop(task_name)
            return {
                "running": thread.is_alive(),
                "output": output 
            }
        else:
            raise ValueError("No such task")
    
    def stop_task(self, task_name: str):
        if task_name in self._tasks:
            _, module = self._tasks[task_name]
            module.stop()
            

    def get_interfaces(self) -> list[ifaces.Interface]:
        return ifaces.get_interfaces()
        
    def list_hosts(self) -> list[db._Host]:
        with db.open() as db_conn:
            return db.get_all_hosts(db_conn)
    
    def get_host(self, host_id: int) -> db._Host | None:
        with db.open() as db_conn:
            return db.get_host(db_conn, host_id)
    
    def list_services(self) -> list[db._Service]:
        with db.open() as db_conn:
            return db.get_all_services(db_conn)
    
    def get_service(self, service_id: int) -> db._Service | None:
        with db.open() as db_conn:
            return db.get_service(db_conn, service_id)
    
    def list_credentials(self) -> list[db._Credential]:
        with db.open() as db_conn:
            return db.get_all_credentials(db_conn)
    
    def get_credential(self, cred_id: int) -> db._Credential | None:
        with db.open() as db_conn:
            return db.get_credential(db_conn, cred_id)
    
    def clear_database(self):
        with db.open() as db_conn:
            db.clear(db_conn)

    def exit(self):
        pass