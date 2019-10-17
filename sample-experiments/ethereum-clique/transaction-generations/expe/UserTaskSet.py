from functools import wraps
from locust import events, TaskSet, task
from time import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
import random
import toml

def geth_locust_task(f):
    '''
    Simple timing wrapper which fires off the necessary
    success and failure events for locust.
    Taken from : https://github.com/egalano/ethereum-load-test/blob/master/locustfile.py
    '''
    @wraps(f)
    def wrapped(*args, **kwargs):
        start_time = time()
        try:
            result = f(*args, **kwargs)
            print(result)
        except Exception as e:
            print('Exception in %s : %s'%(f.__name__, e))
            total_time = int((time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="jsonrpc",
                name=f.__name__,
                response_time=total_time,
                exception=e)
            return False
        else:
            total_time = int((time() - start_time) * 1000)
            events.request_success.fire(
                request_type="jsonrpc",
                name=f.__name__,
                response_time=total_time,
                response_length=0)
        return result
    return wrapped

def get_target_url():
    data = {}
    with open("/tmp/targeted_hosts.toml") as f:
        data.update(toml.load(f))
    return random.choice(data['targets']['urls'])

class UserTaskSet(TaskSet):
    def __init__(self, *args, **kwargs):
        super(UserTaskSet, self).__init__(*args, **kwargs)
        host = get_target_url()
        print("TARGETED URL %s"%(host))
        self.w3 = Web3(Web3.HTTPProvider("http://%s:8545"%(host)))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.accounts = self.w3.eth.accounts

    @geth_locust_task
    @task
    def generate_random_simple_transaction(self):
        print("executing my task")
        rnd = random.Random()
        involved_accounts = rnd.sample(self.accounts, 2)
        from_account = involved_accounts[0]
        to_account = involved_accounts[1]
        transaction_value = rnd.randint(0,10)
        transaction = {
            "from": from_account,
            "to": to_account,
            "value": transaction_value,
            "data": "0x0"
        }
        self.w3.eth.sendTransaction(transaction)