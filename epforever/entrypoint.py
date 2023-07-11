import signal
import sys
from dotenv import dotenv_values
from epforever.ep_http_server import EpHttpServer

proc = None


def exit_now(signum, frame):
    global proc
    print("\nShuting down server...")
    if proc is not None:
        print("\nShuting down serial service...")
        proc.kill()

    sys.exit(0)

def start():
    global proc

    config = dotenv_values(".env")

    server = EpHttpServer(config)
    signal.signal(signal.SIGINT, exit_now)
    server.start()
