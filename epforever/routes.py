import json
import os
from datetime import datetime
from tinydb import TinyDB, Query


class BaseCommand:
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

    def execute(self, post_body: any = None) -> dict:
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


class Datasource_list(BaseCommand):
    def execute(self, post_body: any = None) -> dict:
        p = self.config.get('db_folder')
        files = []
        if p != '':
            files = [
                f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))
            ]

        result = []
        for f in files:
            if f.endswith('json'):
                result.append(f[:-5])

        result.sort()
        return {
            "status_code": 200,
            "content": json.dumps(result)
        }


class Device(BaseCommand):
    def execute(self, post_body: any = None) -> dict:
        if self.path == '/list':
            return self.getDeviceList()

        device_name = self.path[1:]
        return self.getDeviceData(device_name)

    def getDeviceList(self):
        device_list = []
        for device in self.config.get('devices'):
            print("appending value is {}".format(device))
            device_list.append(device)

        return {
            "status_code": 200,
            "content": json.dumps(device_list)
        }

    def getDeviceData(self, device_name: str) -> dict:
        devices = []
        if '_' in device_name:
            devices = device_name.split('_')
        else:
            devices.append(device_name)

        date = self.args.get('date')
        timeval = self.args.get('time')

        if date is None:
            date = 'today'

        if (date == 'today'):
            date = datetime.today().strftime("%Y-%m-%d")

        db_name = f"{date}.json"
        db_path = os.path.join(self.config.get('db_folder'), db_name)

        if not os.path.isfile(db_path):
            return json.dumps(
                {"error": f"Database {db_name} not found on server"}
            )

        db = TinyDB(db_path)
        q = Query()
        datas = []
        resultCounter = []

        for device in devices:
            if timeval is not None:
                result = db.search(
                    (q.device == device) &
                    (q.timestamp > timeval)
                )
            else:
                result = db.search(q.device == device)

            for presult in resultCounter:
                if len(result) != presult.get('count'):
                    # count mismatch
                    print("WARN: mimatch count from {} and presult {}".format(
                        len(result),
                        presult.get('count')
                    ))

            resultCounter.append({
                'device': device,
                'count': len(result)
            })

            datas += result

        results = {
            'result': datas
        }

        return {
            "status_code": 200,
            "content": json.dumps(results)
        }


class Config(BaseCommand):
    def execute(self, post_body: any = None) -> dict:
        curr_config = {}

        if (os.path.exists(self.configFilePath)):
            f = open(self.configFilePath)
            curr_config = json.load(f)
            f.close()
            return {
                "status_code": 200,
                "content": json.dumps(curr_config)
            }

        return {
            "status_code": 404,
            "content": "Not found"
        }


class Nightenv(BaseCommand):
    def execute(self, post_body: any = None) -> dict:
        nightenv_path = self.config.get('nightenv_filepath', '')
        if nightenv_path == '':
            print("warning no night environment file provided in config.json")
            return 'KO'

        if not os.path.exists(nightenv_path):
            print("warning nightenv file does not exists")
            return '{0:.2f}'.format(0)

        env_content = ()
        with open(nightenv_path) as f:
            env_content = f.readlines()
            f.close()

        amount = 0
        length = 0

        for line in env_content:
            value = float(line.split('=')[1])
            # only take it if it is greater than zero
            if value > 0:
                length += 1
                amount += value

        if amount and length > 0:
            result = amount / length
            return '{0:.2f}'.format(result)

        return 0
