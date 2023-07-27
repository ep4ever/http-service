import os
import sys
import json

from epforever.ep_request_handler import EpRequestHandler
from epforever.handlers.tinydb_routes import *  # noqa: F403,F401


class TinyDBHandler(EpRequestHandler):

    def _load_config(self):
        lconfig = EpRequestHandler.CONFIG.get('MAIN_CONFIG_PATH', None)
        if not os.path.isfile(lconfig):
            print("API ERROR: main config.json could not be read")
            sys.exit(1)

        f = open(lconfig)
        self.config = json.load(f)

    def _get_class(self, domain: str):
        try:
            return globals()[domain.capitalize()]
        except KeyError:
            print(f"ERROR: Domain {domain} does not exists")
            return None
