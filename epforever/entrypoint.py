import signal
import sys
import subprocess
import argparse
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


def run_config(config):
    print('todo: ask user for editing .env file')
    pass


def start():
    global proc

    parser = argparse.ArgumentParser(
        description='Optional ep4ever http service arguments'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='If provided will start the configuration wizard'
    )
    parser.add_argument(
        '--withserial',
        action='store_true',
        help='If provided will start the serial service in a sub process'
    )
    args = parser.parse_args()
    config = dotenv_values(".env")

    if args.config:
        return run_config(config)

    if args.withserial:
        serial_service = config.get('SERIAL_SERVICE_PATH')
        proc = subprocess.Popen([serial_service])

    server = EpHttpServer(config)
    signal.signal(signal.SIGINT, exit_now)
    server.start()
