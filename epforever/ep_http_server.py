from http.server import HTTPServer
from socketserver import ThreadingMixIn
import base64
import ssl
import sys

from epforever.ep_request_handler import EpRequestHandler
from epforever.handlers.tinydb_handler import TinyDBHandler
from epforever.handlers.mariadb_handler import MariaDBHandler


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class EpHttpServer:
    httpd: HTTPServer
    config: dict

    def __init__(self, config: dict):
        self.config = config
        EpRequestHandler.CONFIG = self.config

    def start(self):
        server_address = ('', int(self.config.get('PORT', 8180)))
        if (
                self.config.get('USER', None) and
                self.config.get('PASSWORD', None)
        ):
            auth = ''.join(
                [
                    self.config.get('USER'),
                    ':',
                    self.config.get('PASSWORD')
                ]
            )
            EpRequestHandler.KEY = base64.b64encode(auth.encode('utf-8'))

        # no threading available on windows (it runs) ?
        # self.httpd = HTTPServer(server_address, EpRequestHandler)
        if self.config.get('MODE') == 'tiny':
            self.httpd = ThreadedHTTPServer(server_address, TinyDBHandler)
        elif self.config.get('MODE') == 'maria':
            self.httpd = ThreadedHTTPServer(server_address, MariaDBHandler)
        else:
            print("ERR: .env MODE key is missing. Must be tiny or maria value")
            sys.exit(1)

        if int(self.config.get('USE_SSL', 0)) == 1:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            crtfile = self.config.get('SSL_CRT', 'server.crt')
            keyfile = self.config.get('SSL_KEY', 'server.key')

            context.load_cert_chain(crtfile, keyfile)
            self.httpd.socket = context.wrap_socket(
                self.httpd.socket,
                server_side=True
            )

        print(f"Server is running at {server_address[1]}")
        self.httpd.serve_forever()
