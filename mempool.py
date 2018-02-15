#! /usr/bin/env python3

"""This implements the global transaction mempool. This is a node that listens
for submitted transactions, and stores all of them indefinitely. It is now
assumed that there is only a single such node, there could be many that
synchronize.
It stores, validates and updates the full blockchain, and keeps track of
which block which transaction is in. On demand it can serve a list of
unprocessed transactions.

/pushtx(tx)       # post json
/unprocessed      # json of all unprocessed transactions
/balance(address)

Later (if needed) /whichblock(txid)
"""

from flask import Flask, request
import sqlite3
import os
import json
import sys
import getopt
import requests
from config import TRACKER_ADDRESS, MEMPOOL_ADDRESS, DIFFICULTY
from transaction import Transaction
from blockchain import BlockChain
from node import running, chainlength

mempool = Flask(__name__)
mempool.blockchain = BlockChain()
mempool.transactions = None # sqlite3.connect("")

@mempool.route('/pushtx', methods=['PUT'])
def pushtx():
    tx = Transaction.from_json(request.get_json())
    if not tx.is_valid():
        return "Invalid transaction; ignoring"
    if not exists(tx, mempool.transactions):
        insert(tx, mempool.transactions)
        return "received transaction %s" % (tx.uuid)
    else:
        return "duplicate transaction; ignoring"

def exists(tx, db):
    c = db.execute(
        "select count(*) from transactions where uuid=?;", (tx.uuid,))
    return c.fetchone()[0] != 0
    
def insert(tx, db):
    db.execute(
        """insert into transactions values 
           (:uuid, :from_addr, :to_addr, :amount, :fee, :msg, :signature, NULL)""",
        tx.__dict__)
    db.commit()

def get_unprocessed(db):
    c = db.execute(
        """select uuid, from_addr, to_addr, amount, fee, msg, signature 
           from transactions where block is NULL""")
    return [Transaction(
        **dict(zip(["uuid", "from_addr", "to_addr",
                    "amount", "fee", "msg", "signature"], data))) for data in c]
    
@mempool.route('/unprocessed', methods=['GET'])
def unprocessed():
    """
    Returns a list of unprocessed transactions in the form of a json list 
    of transaction contructor dictionaries. 
    """
    update_blockchain()
    return json.dumps(list(transaction.__dict__
                           for transaction in get_unprocessed(mempool.transactions)))

def update_blockchain():
    """Update the locally stored version of the blockchain by querying the nodes
    and update the database from it."""
    # download/update blockchain
    longest_blockchain = mempool.blockchain
    try:
        nodes = [url for url in
                 requests.get("%s/nodes" % mempool.tracker_url).json()
                 if running(url)]
    except requests.ConnectionError:
        nodes = []
    for node_url in nodes:
        try:
            if chainlength(node_url) > len(longest_blockchain):
                node_blockchain = BlockChain.from_url(
                    "%s/blockchain" % (node_url))
                # TODO Check validity in terms of transactions (balance of each address
                # is non-negative.
                if len(node_blockchain) > len(longest_blockchain) and \
                   node_blockchain.is_valid(DIFFICULTY):
                    longest_blockchain = node_blockchain
        except requests.ConnectionError:
            pass
    # TODO
    # update transaction pool (database): mark/unmark blocks
    # Note that all existing transactions should in theory be in this database.
    # Could assume that the database is up to date w.r.t. the old blockchain and
    # only update for the newer blocks (on starting the mempool the validity will
    # be initialized from the blockchain)
    mempool.blockchain = longest_blockchain

@mempool.route('/balance', methods=['GET'])
def balance():
    update_blockchain()
    address = request.args.get('address')
    # None if not available
    if request.args.get('unconfirmed', 'false') != "true":
        extra_where = " and block is not NULL"
    else:
        extra_where = ""
    # Better from BlockChain or from database?
    received = mempool.transactions.execute(
        "select sum(amount) from transactions where to_addr=?%s;" % extra_where,
        (address,)).fetchone()[0]
    transferred = mempool.transactions.execute(
        "select sum(amount) + sum(fee) from transactions where from_addr=?%s;" % extra_where,
        (address,)).fetchone()[0]
    if received is None:
        received = 0
    if transferred is None:
        transferred = 0
    return str(received - transferred)
    
if __name__ == '__main__':
    opt, remaining = getopt.getopt(sys.argv[1:], "hm:t:d:")
    opt = dict(opt)
    if "-h" in opt:
        print("""Usage: 
        {scriptname} [options]

        Options:
        -h            show this help
        -m <address>  the address (mempool address) on which to run (default {mempool})
        -t <address>  the tracker address (default {tracker})
        -d <db>       transaction database (default transactions.db)

        Note that when host or port are set, the users must be informed, 
        by setting the right MEMPOOL_ADDRESS in config.py or passing the URL
        on the command line.
        """.format(scriptname=os.path.basename(sys.argv[0]),
                   mempool=MEMPOOL_ADDRESS,
                   tracker=TRACKER_ADDRESS))
        sys.exit()

    tracker_address = opt.get("-t", TRACKER_ADDRESS)
    mempool.tracker_url = "http://%s" % tracker_address
    db = opt.get("-d", "transactions.db")
    db_existed = os.path.isfile(db)
    # will be created if it doesn't exist
    mempool.transactions = sqlite3.connect(db)
    if not db_existed:
        mempool.transactions.execute("""
        create table transactions
        (uuid      varchar primary key not null,
         from_addr varchar             not null,
         to_addr   varchar             not null,
         amount    real                not null,
         fee       real                not null,
         msg       varchar             not null,
         signature varchar             not null,
         block     int);""")

    # The local blockchain is empty on startup: set all transactions to unprocessed (no blocks)
    mempool.transactions.execute(
        "update transactions set block = NULL")
    mempool.transactions.commit()
    # LATER: load blockchain and update database
    # data_dir = os.path.join(CHAINDATA_DIR, "mempool")
    # mempool.blockchain = BlockChain.load(data_dir).as_json()
    
    address = opt.get("-m", MEMPOOL_ADDRESS).split(":")
    host, port = address[0], 80 if len(address) == 1 else int(address[1])        
    mempool.run(host=host, port=port)
