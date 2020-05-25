from enoslib.api import play_on
from enoslib.service import Monitoring
from influxdb import InfluxDBClient


class Monitoring(Monitoring):
    def create_database(self, name: str):
        client = InfluxDBClient(self.collector[0].extra["%s_ip" % self.network], 8086, 'admin', 'admin', name)
        client.create_database(name)

    def backup(self, backup_dir=None):
        requests = {
            'cpu': 'SELECT * FROM cpu',
            'net_peerCount': 'SELECT * FROM net_peerCount',
            'eth_tx_pool': 'SELECT * FROM eth_tx_pool',
            'mem': 'SELECT * FROM mem'
        }
        with play_on(pattern_hosts="collector", roles=self._roles
        ) as p:
            for name in requests.keys():
                p.shell(
                    ("docker exec -it influxdb "
                     "influx -database 'metrics' "
                     f"-execute '{requests[name]}' "
                     f"-format csv > /tmp/{name}.csv"),
                    display_name=f"Export {name} metrics to csv")
                p.fetch(
                    display_name=f"Fetch {name} metrics",
                    src=f"/tmp/{name}.csv",
                    dest=f"{backup_dir}/",
                    flat="yes") 
        super().backup(backup_dir)
