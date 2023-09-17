import signal
import sys

from dotenv import dotenv_values

from epforever.ep_http_server import EpHttpServer


def exit_now(signum, frame):
    print("\nShuting down server...")
    sys.exit(0)


def start():
    config = dotenv_values(".env")

    server = EpHttpServer(config)
    signal.signal(signal.SIGINT, exit_now)
    server.start()
