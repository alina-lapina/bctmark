#!/usr/bin/python3

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import yaml

w3 = Web3(HTTPProvider("http://localhost:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
blocks = {}
current_block = w3.eth.getBlock('latest')

while current_block.number != 0:
    transactions = {}
    for transaction in current_block['transactions']:
        receipt = w3.eth.getTransactionReceipt(transaction)
        transactions[transaction.hex()] = {
            'gasUsed': receipt['gasUsed']
        }
    block_to_insert = {
        'hash': current_block.hash.hex(),
        'transactions': transactions
    }
    blocks.update({int(current_block.number): block_to_insert})
    current_block = w3.eth.getBlock(current_block.number-1)

with open('/tmp/blockchain.yaml', 'w') as f:
    yaml.dump(blocks, f)
