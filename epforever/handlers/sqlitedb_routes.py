import sqlite3
import json
from typing import cast
from epforever.handlers.routes import Routes


class BaseSqliteDBRoutes(Routes):

    def getCnx(self):
        dbpath = self.config.get('DB_PATH')
        self.connection = sqlite3.connect(
            "file:{}?mode=ro".format(dbpath),
            uri=True,
            check_same_thread=False
        )
        return self.connection.cursor()

    def closeCnx(self):
        cursor = self.connection.cursor()
        cursor.close()
        self.connection.close()


class Datasource_list(BaseSqliteDBRoutes):
    def execute(self, post_body=None) -> dict:
        cursor = self.getCnx()
        cursor.execute("SELECT DISTINCT DATE(date) AS datelist FROM data")
        records = cursor.fetchall()
        self.closeCnx()

        sources = []
        for record in records:
            sources.append(record[0])

        return {
            "status_code": 200,
            "content": json.dumps(sources)
        }


class Device(BaseSqliteDBRoutes):
    def execute(self, post_body=None) -> dict:
        if self.path == '/list':
            cursor = self.getCnx()
            cursor.execute("SELECT name from device")
            records = cursor.fetchall()
            self.closeCnx()

            devices = []
            for record in records:
                devices.append(record[0])

            return {
                "status_code": 200,
                "content": json.dumps(devices)
            }

        device_name = self.path[1:]
        return self.getDeviceData(device_name, False)

    def getDeviceList(self):
        device_list = []
        devices: list = cast(list, self.config.get('devices'))
        for device in devices:
            device_list.append(device.get('name'))

        return {
            "status_code": 200,
            "content": json.dumps(device_list)
        }

    def getDeviceData(self, device_name: str, isTiny: bool = True) -> dict:
        datas = []
        devices = self._devices_from_name(device_name)
        date = self._date_from_arg(self.args.get('date'))
        timeval = self._time_from_arg(self.args.get('time'))

        sql = self.getDeviceDataSql()
        cursor = self.getCnx()

        for device in devices:
            cursor.execute(sql, (date, device, timeval))
            records = cursor.fetchall()
            result = list()
            for record in records:
                result.append(json.loads(record[0]))
            datas += result

        self.closeCnx()

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

    def getDeviceDataSql(self) -> str:
        return """
        SELECT
            '{' ||
            '"device":' ||
            '"' || d.name || '",' ||
            '"datestamp":' ||
            '"' || DATE(z.date) || '",' ||
            '"timestamp":' ||
            '"' || strftime('%H:%M:%S', z.date) || '",' ||
            '"data":' ||
                '[' ||
                    GROUP_CONCAT(
                        '{' ||
                        '"field":' ||
                        '"' ||
                        f.name ||
                        '"' ||
                        ',' ||
                        '"value":"' ||
                        z.value ||
                        '"}'
                    ) ||
                ']' ||
            '}'
        AS json
        FROM data z
        JOIN device d ON d.id  = z.device_id
        JOIN field f ON f.id = z.field_id
        WHERE DATE(z.date) = ?
        AND d.name = ?
        AND strftime('%H:%M:%S', z.date) > ?
        GROUP BY
            d.name,
            strftime('%H:%M:%S', z.`date`)
        ORDER BY
        strftime('%H:%M:%S', z.`date`)
        """


class Config(BaseSqliteDBRoutes):
    def execute(self, post_body=None) -> dict:
        response = {
            'datas': [],
            'devices': []
        }

        cursor = self.getCnx()

        cursor.execute("SELECT name, port FROM device")
        devices = cursor.fetchall()
        for device in devices:
            response['devices'].append({
                'name': device[0],
                'port': device[1]
            })

        cursor.execute("SELECT name, format from field")
        fields = cursor.fetchall()

        self.closeCnx()

        for field in fields:
            valueFormatter = 'valueFormatterPct'
            if field[1] == 'N':
                valueFormatter = 'valueFormatterNumber'

            response['datas'].append({
                'fieldname': field[0],
                'format': valueFormatter,
                'width': 85
            })

        return {
            "status_code": 200,
            "content": json.dumps(response)
        }


class Nightenv(BaseSqliteDBRoutes):
    def execute(self, post_body=None) -> dict:
        cursor = self.getCnx()

        cursor.execute(
            """
            SELECT value FROM dashboard_view
            WHERE identifier = 'batt_voltage'
            """
        )
        record = cursor.fetchone()

        self.closeCnx()
        return {
            "status_code": 200,
            "content": '{0:.2f}'.format(record[0])
        }
