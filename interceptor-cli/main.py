import formatting as fmt
import requests
import time

_ASCII_ART = """
.___        __                                     __                
|   | _____/  |_  ___________   ____  ____ _______/  |_  ___________ 
|   |/    \   __\/ __ \_  __ \_/ ___\/ __ \\\\____ \   __\/  _ \_  __ \\
|   |   |  \  | \  ___/|  | \/\  \__\  ___/|  |_> >  | (  <_> )  | \/
|___|___|  /__|  \___  >__|    \___  >___  >   __/|__|  \____/|__|   
         \/          \/            \/    \/|__|                      
"""

_HELP_TEXT = f"""
{fmt.underline("Commands")}
- {fmt.bold("help")}: Get help about built-in commands.
- {fmt.bold("info")}: Get info about the current module.
- {fmt.bold("list")}: List available modules.
- {fmt.bold("load/use <name>")}: Set the current module by name.
- {fmt.bold("set <name> <value>")}: Set an argument for the current module.
- {fmt.bold("run/start/go")}: Run the current module in the foreground.
- {fmt.bold("runbg")}: Run the current module in the background.
- {fmt.bold("tasks")}: View all running tasks.
- {fmt.bold("status <task>")}: View the status and previous output of the given task.
- {fmt.bold("follow <task>")}: Attack to the task and follow its output in real time.
- {fmt.bold("stop <task>")}: Stop a currently running task (only applies to certain tasks).
- {fmt.bold("if")}: Show a list of all available network interfaces.
- {fmt.bold("hosts")}: Display all hosts stored in the database.
- {fmt.bold("host <id>")}: Display host with given ID.
- {fmt.bold("services")}: Display all services stored in the database.
- {fmt.bold("service <id>")}: Display service with given ID.
- {fmt.bold("credentials/creds")}: Display all credentials stored in the database.
- {fmt.bold("credential/cred <id>")}: Display credential with given ID.
- {fmt.bold("resetdb")}: Remove all data from the database.
- {fmt.bold("quit/exit")}: Exit Interceptor
"""

class ArgumentNotSetException(Exception):
    def __init__(self, argument: str):
        super().__init__(f"Required argument <{argument}> not given.")

class TerminalApplication:
    def __init__(self, api_url= "http://127.0.0.1:8080", prompt = "CMD ({})> ", init_cmds = []):
        self._api_url = api_url
        self._running = False
        self._prompt = prompt
        self._current_module = None
        self._set_args = {}
        self._init_cmds = init_cmds
        self._CMD_FUNCS = {
            "help": self._print_help,
            "info": self._print_module_info,
            "list": self._list_modules,
            "load": self._load_module,
            "use": self._load_module,
            "set": self._set_option,
            "run": self._run_module,
            "start": self._run_module,
            "go": self._run_module,
            "runbg": self._run_bg,
            "tasks": self._list_tasks,
            "status": self._print_task_status,
            "follow": self._follow_task,
            "stop": self._stop_task,
            "if": self._list_interfaces,
            "hosts": self._list_hosts,
            "host": self._show_host,
            "services": self._list_services,
            "service": self._show_service,
            "credentials": self._list_creds,
            "creds": self._list_creds,
            "credential": self._show_cred,
            "cred": self._show_cred,
            "resetdb": self._reset_db,
            "exit": self._exit,
            "quit": self._exit
        }

    def run(self):
        self._running = True
        self._display_banner()
        res = requests.get(f"{self._api_url}/module/info")
        if res.status_code == 200:
            module_info = res.json()
            self._current_module = module_info["name"]
        self._main_loop()

    def _display_banner(self):
        print(_ASCII_ART)
        print("- Author: Joseph Thomas")
        print("- Github: https://github.com/joedthomas2005/interceptor\n")
    
    def _main_loop(self):
        while self._running:
            command = input(self._prompt.format(self._current_module))
            self._run_command(command)

    def _run_command(self, command: str):
        cmd, args = self._split_command(command)
        if cmd in self._CMD_FUNCS:
            try:
                self._CMD_FUNCS[cmd](*args)
            except Exception as e:
                print(fmt.error(e))
        else:
            print(fmt.error(f"Command {cmd} not found."))

    def _split_command(self, command: str) -> tuple[str, list]:
        parts = command.split(' ')
        return (parts[0], parts[1:])
    
    def _list_modules(self, *_):
        for module in requests.get(f"{self._api_url}/modules").json()["modules"]:
            print(module["name"])
    
    def _load_module(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("name")
        res = requests.get(f"{self._api_url}/modules/{args[0]}")
        if res.status_code == 404:
            print(fmt.error(f'Module "{args[0]}" not found.'))
        else:
            self._current_module = args[0]
            self._set_args.clear()
    
    def _set_option(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("name")
        elif len(args) < 2:
            raise ArgumentNotSetException("value")
        self._set_args[args[0]] = ' '.join(args[1:])
    
    def _print_help(self, *_):
        print(_HELP_TEXT)
    
    def _print_module_info(self, *_):
        if self._current_module:
            info = requests.get(f"{self._api_url}/modules/{self._current_module}").json()
            info_text = f"{fmt.bold(fmt.underline(info['name']))}\n"
            info_text += info["description"] + '\n\n'
            info_text += f"{fmt.underline('Arguments')}\n"
            for arg in info["args"]:
                if arg['required']:
                    info_text += fmt.bold(fmt.red('! '))
                else:
                    info_text += '- '
                info_text += f"{arg['name']} ({fmt.italic(arg['type'])}): "
                if arg['name'] in self._set_args:
                    info_text += self._set_args[arg['name']]
                else:
                    info_text += arg['default']
                info_text += '\n'
            print(info_text)
        else:
            print(fmt.error("No module loaded."))
    
    def _run_module(self, *_):
        if self._current_module:
            res = requests.post(f"{self._api_url}/modules/{self._current_module}/start", self._set_args)
            if res.status_code == 200:
                task_name = res.text
                running = True
                while running:
                    res = requests.get(f"{self._api_url}/tasks/{task_name}")
                    if res.status_code == 200:
                        status = res.json()
                        if len(status["output"]) > 0:
                            print(status["output"], end='')
                        running = status["running"]
                    else:
                        print(fmt.error(f"Error {res.status_code}: {res.text}"))
                        running = False
                    time.sleep(0.25)
            elif res.status_code == 404:
                print(fmt.error("Module not found."))
            else:
                print(fmt.error(f"Error {res.status_code}: {res.text}"))
        else:
            print(fmt.error("No module selected..."))
    
    def _run_bg(self, *_):
        if self._current_module:
            res = requests.post(f"{self._api_url}/modules/{self._current_module}/start", self._set_args)
            if res.status_code == 200:
                task_name = res.text
                print(fmt.success(f"Started task {fmt.bold(task_name)}"))
            elif res.status_code == 404:
                print(fmt.error("Module not found."))
            else:
                print(fmt.error(f"Error {res.status_code}: {res.text}")) 
        else:
            print(fmt.error("No module selected..."))
    
    def _list_tasks(self, *_):
        for task in requests.get(f"{self._api_url}/tasks").json()["tasks"]:
            print(task["name"])
        
    def _print_task_status(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("task")
        res = requests.get(f"{self._api_url}/tasks/{args[0]}")
        if res.status_code == 404:
            print(fmt.error(f"Task {args[0]} not found"))
        else:
            status = res.json()
            print(f"{fmt.bold('Running')}: {status['running']}")
            print(fmt.bold(fmt.underline("Output")))
            print(status["output"])
    
    def _follow_task(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("task")
        running = True
        while running:
            res = requests.get(f"{self._api_url}/tasks/{args[0]}")
            if res.status_code == 200:
                status = res.json()
                if len(status["output"]) > 0:
                    print(status['output'], end='')
                running = status["running"]
                time.sleep(0.25)
            elif res.status_code == 404:
                print(fmt.error("Task not found."))
                running = False
            else:
                print(fmt.error(f"Error {res.status_code}: {res.text}"))
                running = False
    
    def _stop_task(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("task")
        res = requests.post(f"{self._api_url}/tasks/{args[0]}/stop")
        if res.status_code == 200:
            print(fmt.success(f"Task {fmt.bold(args[0])} is stopping."))
        elif res.status_code == 404:
            print(fmt.error("Task not found."))
        else:
            print(fmt.error(f"Error {res.status_code}: {res.text}"))
            
    def _list_interfaces(self, *_):
        res = requests.get(f"{self._api_url}/interfaces")
        interfaces = res.json()['interfaces']
        for interface in interfaces:
            print(fmt.underline(interface["name"]))
            print(f"\tIPv4: {interface['ipv4']}")
            print(f"\tMAC: {interface['mac']}")
            
    def _list_hosts(self, *_):
        for host in requests.get(f"{self._api_url}/hosts").json()["hosts"]:
            print(f"ID: {host['id']}")
            print(f"\tIPv4: {host['ipv4']}")
            print(f"\tIPv6: {host['ipv6']}")
            print(f"\tMAC: {host['mac']}")
    
    def _show_host(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("id")
        res = requests.get(f"{self._api_url}/hosts/{args[0]}")
        if res.status_code == 404:
            print(fmt.error("No such host."))
        else:
            host = res.json()['host']
            print(f"ID: {host['id']}")
            print(f"\tIPv4: {host['ipv4']}")
            print(f"\tIPv6: {host['ipv6']}")
            print(f"\tMAC: {host['mac']}")
    
    def _list_services(self, *_):
        for service in requests.get(f"{self._api_url}/services").json()["services"]:
            print(f"ID: {service['id']}")
            print(f"\tHost ID: {service['host_id']}")
            print(f"\tTransport Protocol: {service['transport_protocol']}")
            print(f"\tPort: {service['port']}")
    
    def _show_service(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("id")
        res = requests.get(f"{self._api_url}/services/{args[0]}")
        if res.status_code == 404:
            print(fmt.error("No such service."))
        else:
            service = res.json()['service']
            print(f"ID: {service['id']}")
            print(f"\tHost ID: {service['host_id']}")
            print(f"\tTransport Protocol: {service['transport_protocol']}")
            print(f"\tPort: {service['port']}")
    
    def _list_creds(self, *_):
        for cred in requests.get(f"{self._api_url}/credentials").json()["credentials"]:
            print(f"ID: {cred['id']}")
            print(f"Service ID: {cred['service_id']}")
            print(f"Login Name: {cred['login_name']}")
            print(f"Credential: {cred['credential']}")
    
    def _show_cred(self, *args):
        if len(args) < 1:
            raise ArgumentNotSetException("id")
        res = requests.get(f"{self._api_url}/credentials/{args[0]}")
        if res.status_code == 404:
            print(fmt.error("No such credential."))
        else:
            cred = res.json()['credential']
            print(f"ID: {cred['id']}")
            print(f"Service ID: {cred['service_id']}")
            print(f"Login Name: {cred['login_name']}")
            print(f"Credential: {cred['credential']}")
    
    def _reset_db(self, *_):
        warning = fmt.red(fmt.bold("Are you sure you want to reset the database? (y/N) "))
        if input(warning).lower() == 'y':
            requests.post(f"{self._api_url}/db-reset")
            print(fmt.info("Database cleared."))

    def _exit(self, *_):
        self._running = False

if __name__ == "__main__":
    app = TerminalApplication()
    app.run()