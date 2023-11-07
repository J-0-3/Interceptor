# Interceptor
A general purpose network exploitation framework for capturing and filtering traffic, harvesting credentials, and performing various types of host exploitation and enumeration.  

## Features
- Intercepting network traffic using ARP spoofing.
- Scanning for live hosts using ping sweeps and ARP scanning.
- Modifying and forwarding packets on the wire.
- Centralised database of captured hosts and credentials.
- Web interface.
- Command line interface.
- A simple module system allowing for easy extensibility.
- REST API backend.

## Usage
The project is split into three parts, the core functionality being implemented in [interceptor-core](/interceptor-core). This is a flask application, and must be run on port 8080. To install all dependencies and run the core service: use the following commands:

- Move into the core service directory: `cd interceptor-core`
- Install dependencies: `pip install -r requirements.txt`
- Run the application: `flask run --port 8080`

The service should now be running on port 8080. 

To interact with the service, you can either use the CLI or the web based interface. 

### CLI
The CLI frontend is located in [interceptor-cli](/interceptor-cli), and can be run with the following commands:

- Move into the directory: `cd interceptor-cli`
- Install dependencies: `pip install -r requirements.txt`
- Run the program: `python main.py`

### Web Interface
The web frontend is located in [interceptor-web](/interceptor-web), and is just a static web app, so can be run using any HTTP server of your choice. 
To run it using the built in Python HTTP server you can use the command: `python -m http.server 80 -b 127.0.0.1`.
