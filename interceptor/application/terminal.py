from interceptor.application.core import CoreApplication
import interceptor.io as io
import interceptor.formatting as fmt
import threading

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
- {fmt.bold("list <category>")}: List all modules in category (e.g. "list arp").
- {fmt.bold("load <name>")}: Load a module by name.
- {fmt.bold("set <name> <value>")}: Set an argument for a module.
- {fmt.bold("run")}: Run the current module in the foreground.
- {fmt.bold("runbg")}: Run the current module in the background.
- {fmt.bold("tasks")}: View all running tasks.
- {fmt.bold("status <task>")}: View the status and previous output of the given task.
- {fmt.bold("follow <task>")}: Attack to the task and follow its output in real time.
- {fmt.bold("hosts")}: Display all hosts stored in the database.
- {fmt.bold("host <id>")}: Display host with given ID.
- {fmt.bold("services")}: Display all services stored in the database.
- {fmt.bold("service <id>")}: Display service with given ID.
- {fmt.bold("credentials/creds")}: Display all credentials stored in the database.
- {fmt.bold("credential/cred <id>")}: Display credential with given ID.
- {fmt.bold("quit/exit")}: Exit Interceptor
"""

class TerminalApplication:
    def __init__(self, application: CoreApplication, prompt = "CMD ({})> ", init_cmds = []):
        self._application = application
        self._running = False
        self._prompt = prompt
        self._init_cmds = init_cmds

    def run(self):
        self._running = True
        self._display_banner()
        self._main_loop()

    def _display_banner(self):
        print(_ASCII_ART)
        print("- Author: Joseph Thomas")
        print("- Github: https://github.com/joedthomas2005/interceptor\n")
    
    def _main_loop(self):
        while self._running:
            command = input(self._prompt.format(self._application.current_module_name))
            self._run_command(command)

    def _run_command(self, command: str):
        cmd, args = self._split_command(command)
        match cmd:
            case "help":
                print(_HELP_TEXT)
            case "info":
                info = self._application.module_info
                info_text = f"{fmt.bold(fmt.underline(self._application.current_module_name))}\n"
                info_text += info["description"] + '\n\n'
                info_text += f"{fmt.underline('Arguments')}\n"
                for arg in info["args"]:
                    info_text += f"- {arg['name']} ({fmt.italic(arg['type'])}): {arg['value']}\n"
                print(info_text)
            case "load":
                self._application.load_module(args[0])
            case "set":
                self._application.set_option(args[0], args[1])
            case "list":
                for module in self._application.list_modules(*args):
                    print(module)
            case "run":
                if self._application.current_module_name:
                    self._application.start_module()
                    while (status := self._application.get_task_status(self._application.current_module_name))['running']:
                        if len(status["output"]) > 0:
                            print(status["output"], end='')
                    print(status["output"], end='')
                else:
                    print(fmt.error("No module selected..."))
            case "runtask":
                self._application.start_module()
                print(fmt.info(f"Started background task {self._application.current_module_name}"))
            case "tasks":
                for task in self._application.get_tasks():
                    print(task)
            case "follow":
                if args[0] in self._application.get_tasks():
                    while (status := self._application.get_task_status(args[0]))['running']:
                        if len(status["output"]) > 0:
                            print(status['output'], end='')
                    print(status['output'], end='')
                else:
                    print(fmt.error("No such task."))
            case "status":
                if args[0] in self._application.get_tasks():
                    status = self._application.get_task_status(args[0])
                    print(f"{fmt.bold('Running')}: {status['running']}")
                    print(fmt.bold(fmt.underline("Output")))
                    print(status["output"])
                else:
                    print(fmt.error("No such task."))
            case "hosts": 
                for host in self._application.list_hosts():
                    print(host)
            case "host":
                print(self._application.get_host(int(args[0])))
            case "services":
                for service in self._application.list_services():
                    print(service)
            case "service":
                print(self._application.get_service(int(args[0])))
            case "creds"|"credentials":
                for cred in self._application.list_credentials():
                    print(cred)
            case "cred"|"credential":
                print(self._application.get_credential(int(args[0])))
            case "quit"|"exit":
                self._running = False

    def _split_command(self, command: str) -> tuple[str, list]:
        parts = command.split(' ')
        return (parts[0], parts[1:])