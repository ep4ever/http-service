from datetime import datetime


class Routes:
    configFilePath: str

    def __init__(self, path: str, query: str, config: dict):
        self.path = path
        if self.path.count('/') > 1:
            raise ValueError(
                f"composed path is not yet supported: {self.path}"
            )

        self.query = query
        self.args = self._query_to_args()
        self.config = config

    def execute(self) -> dict:
        return self.args

    def _query_to_args(self):
        args = {}
        tokens = self.query.split('&')

        for token in tokens:
            k = token.split('=')
            if (k[0] == ''):
                continue
            args[k[0]] = k[1]

        return args

    def _devices_from_name(self, device_name: str):
        devices = []
        if '_' in device_name:
            devices = device_name.split('_')
        else:
            devices.append(device_name)

        return devices

    def _date_from_arg(self, in_date) -> str:
        if in_date is None:
            return datetime.today().strftime("%Y-%m-%d")

        return in_date

    def _time_from_arg(self, in_time) -> str:
        if in_time is None:
            return '00:00:00'

        return in_time
