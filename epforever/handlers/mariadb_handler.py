from ep_request_handler import EpRequestHandler
from handlers.mariadb_routes import *  # noqa: F403,F401


class MariaDBHandler(EpRequestHandler):

    def _load_config(self):
        self.config = EpRequestHandler.CONFIG

    def _get_class(self, domain: str):
        try:
            return globals()[domain.capitalize()]
        except KeyError:
            print(f"ERROR: Domain {domain} does not exists")
            return None
