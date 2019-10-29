from ast import literal_eval
from bctmark.services.types.blockchain_service import BlockchainService, Address
from enoslib.api import play_on, run_ansible, run_command
from enoslib.host import Host
from enoslib.service.service import Service
from typing import List, Dict
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class EthGethClique(Service, BlockchainService):
    def __init__(self, bootnodes: List[Host], peers: List[Host], extra_vars=None, **kwargs):
        BlockchainService.__init__(self, bootnodes, peers, extra_vars, **kwargs)

    def deploy(self):
        _playbook = os.path.join(CURRENT_PATH, "eth_geth_clique", "eth_geth_clique.yml")
        run_ansible([_playbook], roles=self.roles, extra_vars=self.extra_vars)
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.pip(display_name="Installing Web3", name="web3")
            p.apt(display_name="Installing snap package manager", name="snapd")
            p.shell("snap install solc")


    def destroy(self):
        super()
        pass

    def backup(self):
        super()
        pass

    def create_n_accounts(self, host: Host, password: str = 'password', n: int = 1):
        if not (host in self.bootnodes or host in self.peers):
            raise Exception("Host %s is neither in bootnodes or peers" % host.address)
        rq_res = run_command(
            "repeat %s " % n + \
            "geth --exec \"personal.newAccount(\'%s\')\" --verbosity 0 attach http://localhost:8545" % password,
            pattern_hosts=host.alias,
            roles=self.roles
        )
        print(rq_res['ok'])

    def get_accounts(self) -> Dict[str, List[Address]]:
        accounts = {}
        rq_accounts_res = run_command(
            "geth --exec \"eth.accounts\" --verbosity 0 attach http://localhost:8545",
            pattern_hosts="all",
            roles=self.roles
        )

        for host, result in rq_accounts_res['ok'].items():
            accounts[host] = literal_eval(result['stdout'])

        return accounts

    def get_nodes(self) -> List[Host]:
        return self.bootnodes + self.peers

    def make_every_accounts_default(self):
        _playbook = os.path.join(
            CURRENT_PATH,
            "eth_geth_clique",
            "use_utils_pb.yml"

        )
        run_ansible(
            [_playbook],
            roles=self.roles,
            extra_vars={'playbook_to_include': 'make_accounts_default.yml'}
        )
        run_ansible(
            [_playbook],
            roles=self.roles,
            extra_vars={'playbook_to_include': 'unlock_accounts.yml'}
        )
