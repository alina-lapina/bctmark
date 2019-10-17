from locust import Locust, events
from UserTaskSet import UserTaskSet
from influxdb import InfluxDBClient
from datetime import datetime
from web3 import Web3
from web3.middleware import geth_poa_middleware
import toml

MIN_WAIT = 500
MAX_WAIT = 1000

def load_influxdb_url():
    data = {}
    with open("/tmp/targeted_hosts.toml") as f:
        data.update(toml.load(f))
    return data['influxdb']['urls'][0]

class EthUserBehavior(Locust):
    task_set = UserTaskSet
    min_wait = MIN_WAIT
    max_wait = MAX_WAIT

    def __init__(self):
        events.request_success += self.hook_request_success
        #events.request_failure += self.hook_request_fail
        self.client = InfluxDBClient(load_influxdb_url(), 8086, 'admin', 'admin', 'locust')
        self.client.create_database('locust')

    # inspired from https://www.blazemeter.com/blog/locust-monitoring-with-grafana-in-just-fifteen-minutes/
    def hook_request_success(self, request_type, name, response_time, **kw):
        json_body = [{
            "measurement": "transaction_resp_time",
            "time": datetime.now().isoformat(),
            "fields": {
                "request_type": request_type,
                "name": name,
                "response_time": int(response_time)
            }
        }]
        self.client.write_points(json_body)