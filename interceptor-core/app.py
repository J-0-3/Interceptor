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

@_api.route("/hosts/<id>")
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

@_api.route("/services/<id>")
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

@_api.route("/credentials/<id>")
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

@_api.route("/modules/<module>")
def get_module_info(module: str):
    try:
        info = _application.get_module_info(module)
    except ModuleNotFoundError:
        return ("No such module", 404)
    return info

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

@_api.route("/tasks/<task>")
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

@_api.route("/tasks/<task>/stop", methods=["POST"])
def stop_task(task):
    try:
        _application.stop_task(task)
    except ValueError:
        return ("Task not found", 404)
    return ("Task stopping", 200)
    
@_api.route("/modules/<module>/start", methods=["POST"])
def run_module(module: str):
    args = request.form
    try:
        task_name = _application.start_module(module, args)
    except ModuleNotFoundError:
        return ("No such module", 404)
    except TypeError:
        return ("Bad argument type", 400)
    return (task_name, 200)

@_api.route("/interfaces")
def get_interfaces():
    interfaces = _application.get_interfaces()
    return {
        "interfaces": [
            {
                "name": iface.name,
                "ipv4": str(iface.ipv4_addr),
                "mac": str(iface.mac_addr)
            } for iface in interfaces
        ]
    }

@_api.route("/db-reset", methods=["POST"])
def clear_database():
    _application.clear_database()
    return ("Database cleared", 200)