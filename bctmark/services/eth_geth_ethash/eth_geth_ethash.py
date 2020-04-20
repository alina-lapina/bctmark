from ast import literal_eval
from bctmark.services.types.blockchain_service import BlockchainService, Address
from enoslib.api import play_on, run_ansible, run_command
from enoslib.host import Host
from enoslib.service.service import Service
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class EthGethEthash(Service, BlockchainService):
    def __init__(self, bootnodes: List[Host], peers: List[Host], extra_vars=None, **kwargs):
        BlockchainService.__init__(self, bootnodes, peers, extra_vars, **kwargs)

    def deploy(self):
        _playbook = os.path.join(CURRENT_PATH, "eth_geth_ethash", "eth_geth_ethash.yml")
        run_ansible([_playbook], roles=self.roles, extra_vars=self.extra_vars)
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.pip(display_name="Installing Web3", name="web3")
            p.pip(display_name="Installing py-solc", name="py-solc")
            p.apt(display_name="Installing snap package manager", name="snapd")
            p.shell("snap install solc")
            p.file(
                    src="/snap/bin/solc",
                    dest="/usr/bin/solc",
                    state="link")

    def destroy(self):
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.shell("if pgrep geth; then pkill geth; fi")

    def backup(self, backup_dir = Path.cwd()):
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.pip(display_name="Installing PyYAML", name="pyyaml")
            p.copy(
                display_name="Copy blockchain backup python script",
                src=os.path.join(CURRENT_PATH, "files", "backup.py"),
                dest="/tmp/backup.py"
            )
            p.command("python3 /tmp/backup.py")
            now_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            p.fetch(src="/tmp/blockchain.yaml", dest=f"{backup_dir}/backup-ethereum-{now_str}")

    def create_n_accounts(self, host: Host, password: str = 'password', n: int = 1):
        if not (host in self.bootnodes or host in self.peers):
            raise Exception("Host %s is neither in bootnodes or peers" % host.address)
        rq_res = run_command(
            "for i in {1..%s};" % n + \
            "do geth --exec \"personal.newAccount(\'%s\')\" --verbosity 0 attach http://localhost:8545;" % password + \
            "done;",
            pattern_hosts=host.alias,
            roles=self.roles
        )
        print("###### RESULT")
        print(rq_res['ok'])
        return rq_res['ok']

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
            "eth_geth_ethash",
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
