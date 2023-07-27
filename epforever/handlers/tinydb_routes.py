import os
import json
import tempfile
from tinydb import TinyDB, Query
from epforever.handlers.routes import Routes


class Datasource_list(Routes):
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


class Device(Routes):
    def execute(self, post_body: any = None) -> dict:
        if self.path == '/list':
            return self.getDeviceList()

        device_name = self.path[1:]
        return self.getDeviceData(device_name)

    def getDeviceList(self):
        device_list = []
        for device in self.config.get('devices'):
            device_list.append(device.get('name'))

        return {
            "status_code": 200,
            "content": json.dumps(device_list)
        }

    def getDeviceData(self, device_name: str, isTiny: bool = True) -> dict:
        devices = self._devices_from_name(device_name)
        date = self._date_from_arg(self.args.get('date'))
        timeval = self.args.get('time')
        datas = []

        db_name = f"{date}.json"
        db_path = os.path.join(self.config.get('db_folder'), db_name)

        if not os.path.isfile(db_path):
            return json.dumps(
                {"error": f"Database {db_name} not found on server"}
            )

        db = TinyDB(db_path)
        q = Query()
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
                    print("WARN: mimatch count from {} and presult {}".format(  # noqa: E501
                        len(result),
                        presult.get('count')
                    ))

            resultCounter.append({
                'device': device,
                'count': len(result)
            })

            datas += result

        datasorted = sorted(
            datas,
            key=lambda data: (data['timestamp'], data['device'])
        )
        results = {
            'result': datasorted
        }

        return {
            "status_code": 200,
            "content": json.dumps(results)
        }


class Config(Routes):
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


class Nightenv(Routes):
    def execute(self, post_body: any = None) -> dict:
        nightenv_path = os.path.join(
            tempfile.gettempdir(),
            '.nightenv'
        )

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

        return '{0:.2f}'.format(0)
