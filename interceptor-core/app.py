from interceptor.internal.core import CoreApplication
from flask import Flask, request

_api = Flask("interceptor-api")
_application: CoreApplication = CoreApplication()

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
    try:
        _application.load_module(module)
    except ModuleNotFoundError:
        return ("Module not found", 404)
    return ("Module loaded", 200)

@_api.route("/module/info")
def get_current_module_info():
    if _application.current_module_name != None:
        return _application.module_info
    return ("No module loaded", 404)

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
    try:
        status = _application.get_task_status(task)
        return {
            "name": task,
            "running": status["running"],
            "output": status["output"]
        }
    except ValueError:
        return ("Task not found", 404)

@_api.route("/run", methods=["POST"])
def run_module():
    _application.start_module()
    return ("Started task", 200)

@_api.route("/db-reset", methods=["POST"])
def clear_database():
    _application.clear_database()
    return ("Database cleared", 200)