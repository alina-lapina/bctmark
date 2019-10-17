from enoslib.api import run_ansible
from enoslib.service.service import Service
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class EthGeth(Service):
    def __init__(self, bootnodes, peers, extra_vars=None, **kwargs):
        self.bootnodes = bootnodes
        self.peers = peers
        self.roles = {}
        self.roles.update(bootnode = bootnodes, peer = peers)
        if "dashboard" in kwargs:
            self.roles.update(dashboard = kwargs["dashboard"])

        self.extra_vars = {}
        if extra_vars is not None:
            self.extra_vars.update(extra_vars)

    def deploy(self):
        _playbook = os.path.join(CURRENT_PATH, "eth_geth", "eth_geth.yml")
        run_ansible([_playbook], roles=self.roles, extra_vars=self.extra_vars)