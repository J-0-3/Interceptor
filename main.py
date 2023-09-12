from interceptor.application.core import CoreApplication
from interceptor.application.terminal import TerminalApplication
import interceptor.application.api as api
import sys

def api_main():
    core = CoreApplication()
    api.run(core)

def terminal_main():
    core = CoreApplication()
    app = TerminalApplication(core)
    app.run()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        api_main()
    else:
        terminal_main()
