import interceptor.formatting as fmt
import requests

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
    def __init__(self, api_url= "http://127.0.0.1:8080", prompt = "CMD ({})> ", init_cmds = []):
        self._api_url = api_url
        self._running = False
        self._prompt = prompt
        self._current_module = None
        self._init_cmds = init_cmds

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
        match cmd:
            case "help":
                print(_HELP_TEXT)
            case "info":
                info = requests.get(f"{self._api_url}/module/info").json()
                if info == {}:
                    print(fmt.error("No module loaded."))
                else:
                    info_text = f"{fmt.bold(fmt.underline(info['name']))}\n"
                    info_text += info["description"] + '\n\n'
                    info_text += f"{fmt.underline('Arguments')}\n"
                    for arg in info["args"]:
                        info_text += f"- {arg['name']} ({fmt.italic(arg['type'])}): {arg['value']}\n"
                    print(info_text)
            case "load":
                res = requests.post(f"{self._api_url}/module/load", data={"module": args[0]})
                if res.status_code == 404:
                    print(fmt.error(f'Module "{args[0]}" not found.'))
                else:
                    self._current_module = args[0]
            case "set":
                requests.post(f"{self._api_url}/set", data = {"name": args[0], "value": args[1]})
            case "list":
                for module in requests.get(f"{self._api_url}/modules").json()["modules"]:
                    print(module["name"])
            case "run":
                if self._current_module:
                    requests.post(f"{self._api_url}/run")
                    while (status := requests.get(f"{self._api_url}/task/{self._current_module}").json())['running']:
                        if len(status["output"]) > 0:
                            print(status["output"], end='')
                    print(status["output"], end='')
                else:
                    print(fmt.error("No module selected..."))
            case "runbg":
                requests.post(f"{self._api_url}/run")
                print(fmt.info(f"Started task {self._current_module}"))
            case "tasks":
                for task in requests.get(f"{self._api_url}/tasks").json()["tasks"]:
                    print(task["name"])
            case "follow":
                if {"name": args[0]} in requests.get(f"{self._api_url}/tasks").json()["tasks"]:
                    while (status := requests.get(f"{self._api_url}/tasks/{args[0]}").json())['running']:
                        if len(status["output"]) > 0:
                            print(status['output'], end='')
                    print(status['output'], end='')
                else:
                    print(fmt.error("No such task."))
            case "status":

                res = requests.get(f"{self._api_url}/task/{args[0]}")
                if res.status_code == 404:
                    print(fmt.error(f"Task {args[0]} not found"))
                else:
                    status = res.json()
                    print(f"{fmt.bold('Running')}: {status['running']}")
                    print(fmt.bold(fmt.underline("Output")))
                    print(status["output"])
            case "hosts": 
                for host in requests.get(f"{self._api_url}/hosts").json()["hosts"]:
                    print(f"ID: {host['id']}\n\tIPv4: {host['ipv4']}\n\tIPv6: {host['ipv6']}\n\tMAC: {host['mac']}")
            case "host":
                host = requests.get(f"{self._api_url}/host/{args[0]}").json()["host"]
                print(f"ID: {host['id']}\n\tIPv4: {host['ipv4']}\n\tIPv6: {host['ipv6']}\n\tMAC: {host['mac']}")
            case "services":
                for service in requests.get(f"{self._api_url}/services").json()["services"]:
                    print(f"ID: {service['id']}\n\tHost ID: {service['host_id']}\n\tTransport Protocol: {service['transport_protocol']}\n\tPort: {service['port']}\n\tService: {service['service']}")
            case "service":
                service = requests.get(f"{self._api_url}/service/{args[0]}").json()["service"]
                print(f"ID: {service['id']}\n\tHost ID: {service['host_id']}\n\tTransport Protocol: {service['transport_protocol']}\n\tPort: {service['port']}\n\tService: {service['service']}")
            case "creds"|"credentials":
                for cred in requests.get(f"{self._api_url}/credentials").json()["credentials"]:
                    print(f"ID: {cred['id']}\n\tService ID: {cred['service_id']}\n\tLogin Name: {cred['login_name']}\n\tCredential: {cred['credential']}")
            case "cred"|"credential":
                cred = requests.get(f"{self._api_url}/credential/{args[0]}").json()["credential"]
                print(f"ID: {cred['id']}\n\tService ID: {cred['service_id']}\n\tLogin Name: {cred['login_name']}\n\tCredential: {cred['credential']}")
            case "quit"|"exit":
                self._running = False

    def _split_command(self, command: str) -> tuple[str, list]:
        parts = command.split(' ')
        return (parts[0], parts[1:])
    
if __name__ == "__main__":
    app = TerminalApplication()
    app.run()