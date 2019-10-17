from bctmark.services.bctmark_worker.bctmark_worker import BCTMarkWorker
from bctmark.services.types.blockchain_service import BlockchainService, Address
from enoslib.api import play_on, run_ansible
from enoslib.host import Host
from typing import List, Dict
import os
import errno
import yaml

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


def _load_transactions_from_file(transactions_file):
    with open(transactions_file, 'r') as f:
        transactions = yaml.safe_load(f)
    return transactions


def _extract_account_addresses_from_transactions(transactions) -> List[Address]:
    accounts_from = set([t['from'] for t in transactions])
    accounts_to = set([t['to'] for t in transactions])
    return list(accounts_from.union(accounts_to))


def _send_transactions_to_worker(w: Host, trx: List):
    filename = '/tmp/BCTMARK-WORKERS/trx-%s' % w.alias + w.address
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'w') as f:
        yaml.dump(trx, f)

    with play_on(pattern_hosts="all", roles={'target': [w]}) as p:
        p.copy(
            display_name='Send transactions to worker %s' % w.alias,
            src=filename,
            dest='/tmp/transactions_to_replay.yml'
        )


class ReplayManager:
    def __init__(self, bctmark_worker: BCTMarkWorker, transactions_file, blockchain_system: BlockchainService):
        self.transactions = _load_transactions_from_file(os.path.realpath(transactions_file))
        self.addresses_trx_to_replay = _extract_account_addresses_from_transactions(self.transactions)
        self.bs = blockchain_system
        self.bctmark_worker = bctmark_worker

    def replay_transactions(self):
        self._prepare_replay()
        self._dispatch_transactions()
        self.bctmark_worker.run('/tmp/transactions_to_replay.yml')

    def _prepare_replay(self):
        """
        Compare existing the number of addresses in the blockchain system
        and the number of addresses needed in the transactions to replay.
        If needed, create new ones.
        In any cases, replaces the addresses in the transactions to replay
        with addresses in the system.
        """
        existing_addresses = self._get_existing_addresses()
        if len(existing_addresses) < len(self.addresses_trx_to_replay):
            nb_accounts_to_create = len(self.addresses_trx_to_replay) - len(existing_addresses)
            self._create_n_accounts(nb_accounts_to_create)
        map_addresses = dict(zip(self.addresses_trx_to_replay, self._get_existing_addresses()))
        self._replace_addresses(map_addresses)
        self._gather_private_keys_to(self.bctmark_worker.workers)

    def _dispatch_transactions(self):
        trx_for_workers = self._split_transactions_between_workers()
        for w, trx in trx_for_workers.items():
            _send_transactions_to_worker(w, trx)
        pass

    def _split_transactions_between_workers(self) -> Dict[Host, List]:
        # TODO dispatch by address can be a bit naive ?
        nb_workers = len(self.bctmark_worker.workers)
        addresses = self._get_existing_addresses()
        nb_accounts_by_worker = len(addresses)
        trx_by_worker = {}
        for i in range(nb_workers):
            index_min = i * nb_accounts_by_worker
            index_max = (i + 1) * nb_accounts_by_worker
            trx_by_worker[self.bctmark_worker.workers[i]] = self._get_trx_for_accounts(addresses[index_min:index_max])
        return trx_by_worker

    def _gather_private_keys_to(self, hosts: List[Host]):
        # TODO set timestamp to dest local dir to make it "unique"
        # so I don't have to delete it at every run
        _playbook = os.path.join(CURRENT_PATH, "playbooks", "fetch_private_keys.yaml")
        run_ansible([_playbook], roles=self.bs.roles)

        with play_on(pattern_hosts="all", roles={'hosts': hosts}) as p:
            p.copy(
                display_name='Copy files to bench workers',
                src='/tmp/BCTMARK/',
                dest='/tmp/home/geth/.ethereum/keystore/'
            )
        self.bs.make_every_accounts_default()
        print('ici')

    def _get_existing_addresses(self) -> List[Address]:
        dict_accounts = self.bs.get_accounts()
        addresses = []
        for k, v in dict_accounts.items():
            addresses += v
        return addresses

    def _create_n_accounts(self, n: int):
        nodes = self.bs.get_nodes()
        accounts = []
        for _ in range(n):
            accounts += self.bs.create_n_accounts(nodes[0])
        return accounts

    def _replace_addresses(self, mapping_addresses: Dict[Address, Address]):
        for t in self.transactions:
            t['from'] = mapping_addresses[t['from']]
            t['to'] = mapping_addresses[t['to']]

    def _get_trx_for_accounts(self, addresses: List[Address]) -> List:
        return list(filter(lambda x: x['from'] in addresses or x['to'] in addresses, self.transactions))
