from typing import cast
import MySQLdb
import json

from MySQLdb.connections import Connection
from epforever.handlers.routes import Routes


class BaseMariaDBRoutes(Routes):

    def getCnx(self):
        self.connection: Connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        return self.connection.cursor()

    def closeCnx(self):
        cursor = self.connection.cursor()
        cursor.close()
        self.connection.close()


class Datasource_list(BaseMariaDBRoutes):
    def execute(self) -> dict:
        cursor = self.getCnx()
        cursor.execute("""
            SELECT DATE_FORMAT(datestamp, '%Y-%m-%d')
            FROM diary
            ORDER BY datestamp
        """)
        sources = cursor.fetchall()
        self.closeCnx()

        return {
            "status_code": 200,
            "content": json.dumps(sources)
        }


class Device(BaseMariaDBRoutes):
    def execute(self) -> dict:
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
        datas = []
        devices = self._devices_from_name(device_name)
        date = self._date_from_arg(self.args.get('date'))
        timeval = self._time_from_arg(self.args.get('time'))

        sql = self.getDeviceDataSql()
        cursor = self.getCnx()

        for device in devices:
            cursor.execute(sql, (date, date, device, timeval))
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
            SELECT CONCAT(
                '{',
                '"device":',
                '"', d.name, '",',
                '"datestamp":',
                '"', DATE_FORMAT(DATE(z.date), '%%Y-%%m-%%d'), '",',
                '"timestamp":',
                '"', DATE_FORMAT(TIME(z.date), '%%T'), '",',
                '"data":',
                    '[',
                        GROUP_CONCAT(
                            CONCAT(
                                '{',
                                '"field":',
                                '"',
                                f.name,
                                '"',
                                ',',
                                '"value":"',
                                z.value,
                                '"}'
                            )
                        ),
                    ']',
                '}'
            ) AS json
            FROM data z
            JOIN device d ON d.id  = z.device_id
            JOIN field f ON f.id = z.field_id
            WHERE z.date >= %s && z.date < (%s + INTERVAL 1 DAY)
            AND d.name = %s
            AND DATE_FORMAT(TIME(z.date), '%%T') > %s
            GROUP BY d.name, TIME(z.`date`)
            ORDER BY TIME(z.`date`)
        """


class Config(BaseMariaDBRoutes):
    def execute(self) -> dict:
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


class Nightenv(BaseMariaDBRoutes):
    def execute(self) -> dict:
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


class Consumer(BaseMariaDBRoutes):
    def execute(self) -> dict:
        cursor = self.getCnx()

        cursor.execute(
            """
            SELECT regkey, watts FROM consumer_view
            """
        )
        fields = cursor.fetchall()

        self.closeCnx()
        response = {}

        for field in fields:
            response[field[0]] = field[1]

        return {
            "status_code": 200,
            "content": json.dumps(response)
        }

