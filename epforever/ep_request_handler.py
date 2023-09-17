from http.server import BaseHTTPRequestHandler
import mimetypes
import os
import sys
from urllib.parse import ParseResult, urlparse

from epforever.handlers.routes import Routes


class EpRequestHandler(BaseHTTPRequestHandler):
    """
    override BaseHTTPRequestHandler::server_version
    """
    server_version: str = 'ep4ever 0.1'

    """
    override BaseHTTPRequestHandler::sys_version
    """
    sys_version: str = ''

    KEY: bytes = b''
    CONFIG: dict = {}

    """Ctor"""
    def __init__(self, request, client_address, server):
        self.config: dict = {}
        self.server_addr: str = ''
        # note that post body is actually not handled
        self.post_body: bytes | None = None

        self.__load_web_root()
        self._load_config()

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
        lroot: str = EpRequestHandler.CONFIG.get('WEB_ROOT_PATH', '')
        if not os.path.isdir(lroot):
            print("API ERROR: Missing webroot folder WEB_ROOT_PATH")
            sys.exit(1)

        self.webroot = lroot

    """
    Loads the config object needed by the handler and put it in self.config
    attribute.
    """
    def _load_config(self):
        raise NotImplementedError("_load_config method must be overrided")

    """
    Returns the class that handle routes call
    """
    def _get_class(self):
        raise NotImplementedError("_get_class method must be overrided")

    def _handle_request(self, method: str):
        if self.__needs_auth():
            return

        # reset post body content
        self.post_body = None
        path_tokens: ParseResult = urlparse(self.path)
        response: bytes = b''
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

    def _run_command(
        self,
        path_tokens: ParseResult
    ) -> dict | bool:
        root = path_tokens.path[4:]
        domain = root.split('/')[1]
        Class = self._get_class(domain)  # pyright: ignore
        if not issubclass(Class, Routes):
            print(
                "ERR: Route handler must inherit from epforver.handlers.Routes"
            )
            sys.exit(1)
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
        return instance.execute()

    def __needs_auth(self) -> bool:
        if EpRequestHandler.KEY is None or EpRequestHandler.KEY == b'':
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
        path_tokens: ParseResult
    ) -> bytes:
        response = self._run_command(path_tokens)
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
            return str(response.get('content')).encode('utf-8')

        return str(response).encode('utf-8')

    def _handle_post_api_call(self, path_tokens: ParseResult) -> bytes:
        print("API WARNING: post api call is not implemented yet...")
        content_len = int(str(self.headers.get('Content-Length')))
        self.post_body = self.rfile.read(content_len)
        return self._handle_api_call(path_tokens)

    def _handle_web_call(self, path_tokens: ParseResult) -> bytes:
        if (path_tokens.path == '/'):
            filepath = self.webroot + '/index.html'
        else:
            filepath = self.webroot + path_tokens.path

        content = ''
        with open(filepath, 'rb') as fh:
            content = fh.read()

        self.send_response(200)

        mtype: str = str(mimetypes.guess_type(filepath)[0])
        self.send_header(
            'server_addr',
            self.server_addr
        )
        self.send_header(
            'Content-type',
            mtype
        )
        return content
