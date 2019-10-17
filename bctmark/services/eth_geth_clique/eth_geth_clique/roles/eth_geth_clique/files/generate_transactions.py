#!/usr/bin/env python3

from web3 import Web3
from random import *
import time
import datetime
import logging

logging.basicConfig(filename='generate_transactions.log',level=logging.INFO)

w3 = Web3(Web3.HTTPProvider(endpoint_uri='http://localhost:8545', request_kwargs={'timeout': 100}))

t_start = time.time() 
logging.info("Transactions generation start time : {:s}".format(datetime.datetime.utcfromtimestamp(t_start).strftime("%d/%m/%Y, %H:%M:%S")))
t_end = t_start + 60 * 60 # one hour
logging.info("Transactions generation end time : {:s}".format(datetime.datetime.utcfromtimestamp(t_end).strftime("%d/%m/%Y, %H:%M:%S")))

nbAccounts = len(w3.eth.accounts)

while time.time() < t_end:
    account_from = choice(w3.eth.accounts)
    account_to = choice(w3.eth.accounts)
    w3.personal.unlockAccount(account_from, 'password')
    w3.eth.sendTransaction({'from': account_from, 'to': account_to, 'value': 10})
    logging.info("Transaction sent from {:s}, to {:s}, value {:d}".format(account_from, account_to, 10))