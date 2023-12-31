import os
import json
import tempfile
from typing import cast
from tinydb import TinyDB, Query
from epforever.handlers.routes import Routes
from dotenv import dotenv_values


class Datasource_list(Routes):
    def execute(self) -> dict:
        p: str = str(self.config.get('db_folder'))
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
    def execute(self) -> dict:
        if self.path == '/list':
            return self.getDeviceList()

        device_name = self.path[1:]
        return self.getDeviceData(device_name)

    def getDeviceList(self):
        device_list = []
        devices: list = cast(list, self.config.get('devices'))
        for device in devices:
            device_list.append(device.get('name'))

        return {
            "status_code": 200,
            "content": json.dumps(device_list)
        }

    def getDeviceData(self, device_name: str) -> dict:
        devices = self._devices_from_name(device_name)
        date = self._date_from_arg(self.args.get('date'))
        timeval = self.args.get('time')
        datas = []

        db_name = f"{date}.json"
        db_path = os.path.join(str(self.config.get('db_folder')), db_name)

        if not os.path.isfile(db_path):
            return {
                "status_code": 200,
                "content":  json.dumps(
                    {"error": f"Database {db_name} not found on server"}
                )
            }

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
    def execute(self) -> dict:
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
    def execute(self) -> dict:
        nightenv_path = os.path.join(
            tempfile.gettempdir(),
            '.nightenv'
        )

        if not os.path.exists(nightenv_path):
            print("warning nightenv file does not exists")
            return {
                "status_code": 404,
                "content": '{0:.2f}'.format(0)
            }

        env_content = dotenv_values(nightenv_path)

        amount = 0
        length = 0

        for k, v in env_content.items():
            if "battery_voltage" in k:
                value = float(v)
                # only take it if it is greater than zero
                if value > 0:
                    length += 1
                    amount += value

        result: str = '{0:.2f}'.format(0)
        if amount and length > 0:
            result = '{0:.2f}'.format(amount / length)

        return {
            "status_code": 200,
            "content": result
        }


class Consumer(Routes):
    def execute(self) -> dict:
        return {
            "status_code": 404,
            "content": {}
        }
