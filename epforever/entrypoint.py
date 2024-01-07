import signal
import sys

from dotenv import dotenv_values

from ep_http_server import EpHttpServer


def exit_now(signum, frame):  # pyright: ignore
    print("\nShuting down server...")
    sys.exit(0)


def start():
    config = dotenv_values(dotenv_path=".env")

    server = EpHttpServer(config)
    signal.signal(signal.SIGINT, exit_now)
    server.start()
