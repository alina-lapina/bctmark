from enoslib.service import Monitoring
from influxdb import InfluxDBClient


class Monitoring(Monitoring):
    def create_database(self, name: str):
        client = InfluxDBClient(self.collector[0].extra["%s_ip" % self.network], 8086, 'admin', 'admin', name)
        client.create_database(name)
