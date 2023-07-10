from http.server import BaseHTTPRequestHandler
from socketserver import BaseServer
import os
import sys
import json
import mimetypes
from urllib.parse import urlparse
from epforever.routes import *  # noqa: F403,F401
from epforever.routes import default_config


class EpRequestHandler(BaseHTTPRequestHandler):
    """
    override BaseHTTPRequestHandler::server_version
    """
    server_version: str = 'ep4ever 0.1'

    """
    override BaseHTTPRequestHandler::sys_version
    """
    sys_version: str = ''
    """
    instance attributes
    """
    server_addr: str = ''
    config = None
    """
    qualifier attributes
    """
    KEY = None
    CONFIG: dict = {}

    """Ctor"""
    def __init__(self, request: any, client_address: any, server: BaseServer):
        self.__load_web_root()
        self.__load_config()

        myip = EpRequestHandler.CONFIG.get('SERVER_IP', '127.0.0.1')
        myport = EpRequestHandler.CONFIG.get('SERVER_PORT', '8180')
        scheme = 'http://'
        if int(EpRequestHandler.CONFIG.get('USE_SSL', 0)) == 1:
            scheme = 'https://'

        self.server_addr = '{}{}:{}'.format(scheme, myip, myport)

        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def authenticate(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"ep4ever\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._handle_request('get')

    def do_POST(self):
        self._handle_request('post')

    def __load_web_root(self):
        lroot = EpRequestHandler.CONFIG.get('WEB_ROOT_PATH', '')
        if not os.path.isdir(lroot):
            print("API ERROR: Missing webroot folder WEB_ROOT_PATH")
            sys.exit(1)

        self.webroot = lroot

    def __load_config(self):
        lconfig = EpRequestHandler.CONFIG.get('MAIN_CONFIG_PATH', None)
        if lconfig is None:
            print("API ERROR: Missing config file MAIN_CONFIG_PATH")
            sys.exit(1)

        if not os.path.isfile(lconfig):
            # we write the default configuration file
            curr_config = default_config()
            with open(lconfig, 'w') as file:
                file.write(json.dumps(curr_config, indent=4))
            print(
                "API WARNING: main configuration file created!"
            )

        f = open(lconfig)
        self.config = json.load(f)
        f.close()

    def _handle_request(self, method: str):
        if self.__needs_auth():
            return

        path_tokens = urlparse(self.path)

        if self.config is not None and path_tokens.path.startswith('/api'):
            if method == 'get':
                response = self._handle_api_call(path_tokens)
            if method == 'post':
                response = self._handle_post_api_call(path_tokens)
        else:
            # only get is handled here
            response = self._handle_web_call(path_tokens)

        self.end_headers()
        self.wfile.write(response)

    def _run_command(self, path_tokens: dict, post_body: any = None) -> dict:
        root = path_tokens.path[4:]
        domain = root.split('/')[1]

        try:
            Class = globals()[domain.capitalize()]
        except KeyError:
            print(f"ERROR: Domain {domain} does not exists")
            return False

        try:
            instance = Class(
                path=root[len(domain)+1:],
                query=path_tokens.query,
                config=self.config
            )
            instance.configFilePath = EpRequestHandler.CONFIG.get(
                'MAIN_CONFIG_PATH',
                None
            )
        except ValueError as err:
            print(err)
            return False
        return instance.execute(post_body)

    def __needs_auth(self) -> bool:
        if EpRequestHandler.KEY is None:
            return False

        auth = self.headers.get('Authorization')
        expected = 'Basic '.encode('utf-8') + EpRequestHandler.KEY

        if auth is None or auth.encode('utf-8') != expected:
            self.authenticate()
            self.wfile.write(
                'Unauthorized access'.encode('utf-8')
            )
            return True

        return False

    def _handle_api_call(
        self,
        path_tokens: dict,
        post_body: any = None
    ) -> bytes:
        response = self._run_command(path_tokens, post_body)
        if not response:
            response = "API Error"
            self.send_response(400)
        else:
            self.send_response(200)
            self.send_header(
                'server_addr',
                self.server_addr
            )
            self.send_header('Content-type', 'application/json')

        if isinstance(response, dict):
            return response.get('content').encode('utf-8')

        return response.encode('utf-8')

    def _handle_post_api_call(self, path_tokens: dict) -> bytes:
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        return self._handle_api_call(path_tokens, post_body)

    def _handle_web_call(self, path_tokens: dict) -> bytes:
        if (path_tokens.path == '/'):
            filepath = self.webroot + '/index.html'
        else:
            filepath = self.webroot + path_tokens.path

        content = ''
        with open(filepath, 'rb') as fh:
            content = fh.read()

        self.send_response(200)

        mtype = mimetypes.guess_type(filepath)[0]
        self.send_header(
            'server_addr',
            self.server_addr
        )
        self.send_header(
            'Content-type',
            mtype
        )
        return content
