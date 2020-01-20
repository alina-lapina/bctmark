import re
from abc import ABC, abstractmethod
from enoslib.host import Host
from typing import Dict, List, NewType

Address = NewType('Address', str)


def _declare_peering_network_role(peer: Host):
    ntw_regex = re.compile(r'^ntw\d+$')
    extras = list(peer.extra.keys())
    for extra in extras:
        if ntw_regex.match(extra) is not None:
            peer.extra.update(peering_network=extra)
            break
    if 'peering_network' not in peer.extra:
        if 'ntw_monitoring' in peer.extra:
            peering_network = peer.extra['ntw_monitoring']
        else:
            peering_network = peer.address
        peer.extra.update(peering_network=peering_network)
    return peer


class BlockchainService(ABC):
    @abstractmethod
    def __init__(self, bootnodes: List[Host], peers: List[Host], extra_vars=None, **kwargs):
        self.bootnodes = list(map(_declare_peering_network_role, bootnodes))
        self.peers = list(map(_declare_peering_network_role, peers))
        self.roles = {}
        self.roles.update(bootnode=self.bootnodes, peer=self.peers)
        if "dashboard" in kwargs:
            self.roles.update(dashboard=kwargs["dashboard"])

        self.extra_vars = {}
        if extra_vars is not None:
            self.extra_vars.update(extra_vars)

    @abstractmethod
    def get_accounts(self) -> Dict[str, List[Address]]:
        """
        Return a dict containing, for each host in the system, the address
        of the accounts it manages
        """
        raise NotImplementedError

    @abstractmethod
    def get_nodes(self) -> List[Host]:
        """
        Return the list of all nodes in the network
        """
        raise NotImplementedError

    @abstractmethod
    def create_n_accounts(self, host: Host, password: str = 'password', n: int = 1):
        """
        Create an account on specified host
        :param n: number of accounts to create, default 1
        :param host: the host where the account should be created
        :param password: the account password, default 'password'
        """
        raise NotImplementedError

    @abstractmethod
    def make_every_accounts_default(self):
        """
        Make every accounts of every nodes default provided accounts and restart service
        """
        raise NotImplementedError
