from interceptor.internal.core import CoreApplication
from terminal import TerminalApplication
import api as api
import interceptor.formatting as fmt
import threading
import time

def main():
    print(fmt.info("Connecting to database..."))
    core = CoreApplication()
    print(fmt.info("Starting REST API..."))
    api_thread = threading.Thread(target = api.run, args=(core,))
    api_thread.start()
    print(fmt.success(f"API listening on {fmt.bold('http://127.0.0.1:8080/')}"))
    print(fmt.info("Starting terminal application..."))
    time.sleep(1)
    app = TerminalApplication()
    app.run()

if __name__ == "__main__":
    main()
