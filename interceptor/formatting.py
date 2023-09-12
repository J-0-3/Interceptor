def bold(text: str) -> str:
    return f"\u001b[1m{text}\u001b[22m"
def dim(text: str) -> str:
    return f"\u001b[2m{text}\u001b[22m"
def italic(text: str) -> str:
    return f"\u001b[3m{text}\u001b[23m"
def underline(text: str) -> str:
    return f"\u001b[4m{text}\u001b[24m"
def blink(text: str) -> str:
    return f"\u001b[5m{text}\u001b[25m"
def reverse(text: str) -> str:
    return f"\u001b[7m{text}\u001b[27m"
def hidden(text: str) -> str:
    return f"\u001b[8m{text}\u001b[28m"
def strikethrough(text: str) -> str:
    return f"\u001b[9m{text}\u001b[29m"
def black(text: str) -> str:
    return f"\u001b[30m{text}\u001b[39m"
def red(text: str) -> str:
    return f"\u001b[31m{text}\u001b[39m"
def green(text: str) -> str:
    return f"\u001b[32m{text}\u001b[39m"
def yellow(text: str) -> str:
    return f"\u001b[33m{text}\u001b[39m"
def blue(text: str) -> str:
    return f"\u001b[34m{text}\u001b[39m"
def magenta(text: str) -> str:
    return f"\u001b[35m{text}\u001b[39m"
def cyan(text: str) -> str:
    return f"\u001b[36m{text}\u001b[39m"
def white(text: str) -> str:
    return f"\u001b[37m{text}\u001b[39m"
def info(text: str) -> str:
    return f"{bold('[.]')} {text}"
def error(text: str) -> str:
    return red(f"{bold('[E]')} {text}")
def warn(text: str) -> str:
    return yellow(f"{bold('[!]')} {text}")
def success(text: str) -> str:
    return green(bold('[\u2713]') + f' {text}')
def verbose(text: str) -> str:
    return f"{dim(bold('[V]'))} {dim(text)}"