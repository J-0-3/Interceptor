from interceptor.application.core import CoreApplication
from flask import Flask, request
from threading import Thread

_api = Flask("interceptor-api")
_application: CoreApplication = None

def run(application: CoreApplication):
    global _application 
    _application = application
    _api.run("127.0.0.1", 8080, False)

@_api.route("/hosts")
def get_hosts():
    hosts = _application.list_hosts()
    return {
        "hosts": [
            {
                "id": host.id,
                "ipv4": host.ipv4,
                "ipv6": host.ipv6,
                "mac": host.mac
            } for host in hosts
        ]
    }

@_api.route("/services")
def get_services():
    services = _application.list_services()
    return {
        "services": [
            {
                "id": service.id,
                "host_id": service.host_id,
                "transport_protocol": service.transport_protocol,
                "port": service.port,
                "service": service.service
            } for service in services
        ]
    }

@_api.route("/credentials")
def get_credentials():
    creds = _application.list_credentials()
    return {
        "credentials": [
            {
                "id": cred.id,
                "service_id": cred.service_id,
                "login_name": cred.login_name,
                "credential": cred.credential
            } for cred in creds
        ]
    }

@_api.route("/host/<id>")
def get_host(id):
    host = _application.get_host(id)
    return {
        "host": {
            "id": id,
            "ipv4": host.ipv4,
            "ipv6": host.ipv6,
            "mac": host.mac
        }
    }

@_api.route("/service/<id>")
def get_service(id):
    service = _application.get_service(id)
    return {
        "service": {
            "id": id,
            "host_id": service.host_id,
            "transport_protocol": service.transport_protocol,
            "port": service.port,
            "service": service.service
        }
    }

@_api.route("/credential/<id>")
def get_credential(id):
    cred = _application.get_credential(id)
    return {
        "credential": {
            "id": id,
            "service_id": cred.service_id,
            "login_name": cred.login_name,
            "credential": cred.credential
        }
    }

@_api.route("/modules")
def get_modules():
    category = request.args.get("category", None)
    if category:
        modules = _application.list_modules(category)
    else:
        modules = _application.list_modules()
    return {
        "modules": [
            {
                "name": module
            } for module in modules
        ]
    }

@_api.route("/module/load", methods=["POST"])
def load_module():
    module = request.form.get("module")
    _application.load_module(module)
    return ("Module loaded", 200)

@_api.route("/module/current")
def get_current_module():
    return {
        "module": {
            "name": _application.current_module_name
        }
    }

@_api.route("/module/info")
def get_current_module_info():
    return _application.module_info

@_api.route("/set", methods=["POST"])
def set_argument():
    name = request.form.get("name")
    value = request.form.get("value")
    _application.set_option(name, value)
    return ("Module loaded", 200)

@_api.route("/tasks")
def get_tasks():
    tasks = _application.get_tasks()
    return {
        "tasks": [
            {
                "name": task
            } for task in tasks
        ]
    }

@_api.route("/task/<task>")
def get_task(task):
    status = _application.get_task_status(task)
    return {
        "name": task,
        "running": status["running"],
        "output": status["output"]
    }

@_api.route("/run", methods=["POST"])
def run_module():
    thread = Thread(target = _application.run_module)
    thread.start()
    _application.add_bg_task(thread)
    return ("Started task", 200)