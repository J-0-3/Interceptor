from interceptor.internal.module import Module
from threading import Thread
import interceptor.database as db
import interceptor.io as io
import os

class CoreApplication:
    def __init__(self):
        self._current_module: Module = None
        self._tasks: dict[str, Thread] = {}
        self._init_db()

    def _init_db(self):
        with db.open() as db_conn:
            db.setup(db_conn)

    @property
    def module_info(self) -> dict:
        if self._current_module:
            return self._current_module.info()
        return {}
    
    @property
    def current_module_name(self) -> str:
        if self._current_module:
            return self._current_module.name
        else:
            return None
        
    def load_module(self, module_name: str):
        self._current_module = Module(module_name)
        
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
    
    def start_module(self):
        if self._current_module:
            io.create(self._current_module.name)
            task_thread = Thread(target = self._current_module.run)
            task_thread.start()
            self._tasks[self._current_module.name] = task_thread

    def get_tasks(self):
        return list(self._tasks.keys())
    
    def get_task_status(self, task_name: str) -> dict:
        if task_name in self._tasks:
            thread = self._tasks[task_name]
            output = ""
            while io.available(task_name):
                output += f"{io.read(task_name)}\n"
            if not thread.is_alive():
                self._tasks.pop(task_name)
            return {
                "running": thread.is_alive(),
                "output": output 
            }
        else:
            raise ValueError("No such task")
        
        
    def set_option(self, arg_name: str, value):
        if self._current_module:
            self._current_module.set(arg_name, value)
    
    @property
    def module_running(self) -> bool:
        if self._current_module:
            return self._current_module.running
        return False
    
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