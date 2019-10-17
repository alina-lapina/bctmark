from abc import ABC, abstractmethod
from enoslib.host import Host
from typing import Dict, List, NewType

Address = NewType('Address', str)


class BlockchainService(ABC):
    @abstractmethod
    def __init__(self, bootnodes: List[Host], peers: List[Host], extra_vars=None, **kwargs):
        self.bootnodes = bootnodes
        self.peers = peers
        self.roles = {}
        self.roles.update(bootnode=bootnodes, peer=peers)
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
