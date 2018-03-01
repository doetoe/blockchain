#! /usr/bin/env python3

"""Imports the same node as in node.py and adds transaction and mempool-related
services to it:

provides mempool services (receive and broadcast transactions):

/pushtx(tx)       # post transaction in json format
/unprocessed      # json of all unprocessed transactions
/balance(address)
/confirmations(transaction_id)

"""

import sys
import os
import getopt
import sqlite3
import requests
import json
from flask import request
from node import node, start, active_peers, \
    get_nodedata_dir, helptext, get_host_port, Synchronizer
from transaction import Transaction, TransactionBundle
from address import Address, could_be_valid_address
# should always be TransactionBlockChain or a subclass
from config import BLOCKCHAIN_CLASS, \
    MAX_TRANSACTIONS_PER_BLOCK

db_connection = None # sqlite3.connect("")

# @node.route('/test', methods=['GET'])
# def test():
#     return "test"

@node.route('/pushtx', methods=['PUT'])
def pushtx():
    tx = Transaction.from_json(request.get_json())
    if not tx.is_valid():
        return "Invalid transaction; ignoring"
    if not exists(tx, db_connection):
        insert(tx, db_connection)
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
    
@node.route('/unprocessed', methods=['GET'])
def unprocessed():
    """Returns unprocessed transactions in the form of a json list 
    of transaction contructor dictionaries."""
    # update_blockchain() - update is done in main_process
    return json.dumps(
        list(transaction.__dict__
             for transaction in get_unprocessed(db_connection)))

class TransactionSynchronizer(Synchronizer):
    def __init__(self, db_connection, miner_address):
        self.db_connection = db_connection
        self.miner_address = miner_address
        
    def __update_db_from_blockchain(self, blockchain, add_missing=False):
        """Resets the block ID for each transaction in the mempool database"""
        self.db_connection.execute(
            "update transactions set block = NULL")
        for block in blockchain:
            for tx in block.get_transaction_bundle():
                if add_missing:
                    # add transactions in the blockchain that are not in the
                    # database.
                    # This command may not be standard SQL, but it works in sqlite
                    self.db_connection.execute(
                        """insert or ignore into transactions values 
                        (:uuid, :from_addr, :to_addr, :amount, :fee, :msg, :signature, NULL)""",
                        tx.__dict__)
                self.db_connection.execute(
                    "update transactions set block = ? where uuid = ?",
                    (block.index, tx.uuid))
        self.db_connection.commit()
        
    def next_block_data(self, blockchain, active_peers):
        # Add unprocessed transactions from all peers to database
        for peer in active_peers.keys(): # have to explictly loop over keys:
                                         # does not exacly behave as dict
            try:
                txs = requests.get("http://%s/unprocessed" % peer).json()
            except requests.ConnectionError:
                continue
            for tx in txs:
                # add transactions in the blockchain that are not in the database.
                # This command may not be standard SQL, but it works in sqlite
                self.db_connection.execute(
                    """insert or ignore into transactions values 
                    (:uuid, :from_addr, :to_addr, :amount, :fee, :msg, :signature, NULL)""",
                    tx.__dict__)
            self.db_connection.commit()
        self.__update_db_from_blockchain(blockchain, add_missing=True)

        # c = self.db_connection.execute(
        #     """select uuid, from_addr, to_addr, amount, fee, msg, signature 
        #     from transactions where block is NULL order by fee desc limit ?""",
        #     MAX_TRANSACTIONS_PER_BLOCK)
        c = self.db_connection.execute(
            """select uuid, from_addr, to_addr, amount, fee, msg, signature 
            from transactions where block is NULL order by fee desc""")

        balances = blockchain.get_balances()

        transactions = []
        for data in c:
            tx = Transaction(
                **dict(zip(["uuid", "from_addr", "to_addr",
                            "amount", "fee", "msg", "signature"], data)))
            if balances.get[tx.from_addr] >= tx.amount + tx.fee:
                balances[tx.from_addr] -= tx.amount + tx.fee
                balances[tx.to_addr] += tx.amount
                transactions.append(tx)
                
            if len(transactions) >= MAX_TRANSACTIONS_PER_BLOCK:
                break
        
        msg = "Mined by %s" % self.node_address
        return TransactionBundle(msg, self.miner_address, transactions).as_json()


@node.route('/balance', methods=['GET'])
def balance():
    # update_blockchain() - update is done in main_process
    # NOTE: block rewards and recipients of fees don't end up in the database
    # so we really need the blockchain. Note that the child process of this same
    # node actually has the blockchain, but we don't use it.
    port = request.environ["SERVER_PORT"] # already is a string
    local_blockchain = BLOCKCHAIN_CLASS.load(get_chaindata_dir(port))
    address = request.args.get('address')
    confirmations = int(request.args.get('confirmations', '1'))
    confirmed_balance = local_blockchain.get_balance(address, confirmations)
    received, transferred = None, None
    if confirmations == 0: # also consider unprocessed transactions
        received = db_connection.execute(
            "select sum(amount) from transactions where to_addr=? and block is NULL;",
            (address,)).fetchone()[0]
        transferred = db_connection.execute(
            "select sum(amount) + sum(fee) from transactions where from_addr=? and block is NULL;",
            (address,)).fetchone()[0]
    return str(confirmed_balance + (received or 0) - (transferred or 0))

@node.route('/confirmations', methods=['GET'])
def confirmations():
    # update_blockchain() - update is done in main_process
    uuid = request.args.get('transaction_id', "")
    if uuid == "":
        abort(400)
    block = db_connection.execute(
        "select block from transactions where uuid=?;",
        (uuid,)).fetchone()[0]
    if block is None:
        return "0"
    else:
        port = request.environ["SERVER_PORT"] # already is a string
        chainlen = len(os.listdir(get_chaindata_dir(port)))
        return str(chainlen - block)

def get_database_dir(port, create=False):
    return get_nodedata_dir(port, "", create)

def transaction_helptext(filename):
    return helptext(filename) + \
        """-d <db>       transaction database (default transactions.db)
        -m <address>  miner address to send the fee and the block reward to
                      (gets lost if unspecified, or actually goes to the 
                      address created with seed "host:port"). Instead of an
                      address, a seed may be passed.
        """

def get_db_connection(opt, port):
    """For a database filename db, create the database if it didn't
    exist, set the blocks of all transactions to NULL and return the
    database connection."""
    db = opt.get("-d", "transactions.db")
    db_path = os.path.join(get_database_dir(port, create=True), db)
    db_existed = os.path.isfile(db_path)
    # will be created if it doesn't exist
    db_connection = sqlite3.connect(db_path)
    if not db_existed:
        db_connection.execute("""
        create table transactions
        (uuid      varchar primary key not null,
         from_addr varchar             not null,
         to_addr   varchar             not null,
         amount    real                not null,
         fee       real                not null,
         msg       varchar             not null,
         signature varchar             not null,
         block     int);""")

    # The local blockchain is empty on startup: set all transactions to
    # unprocessed (no blocks)
    db_connection.execute(
        "update transactions set block = NULL")
    db_connection.commit()
    return db_connection

if __name__ == '__main__':
    # options for transaction database. Take care of the unicity of filenames
    # for different nodes.
    opt, remaining = getopt.getopt(sys.argv[1:], "hHp:t:d:m:")
    opt = dict(opt)
    if "-h" in opt:
        print(transaction_helptext(os.path.basename(sys.argv[0])))
        sys.exit()

    host, port = get_host_port(opt)
    miner_address = opt.get("-m", "%s:%d" % (host, port))
    if not could_be_valid_address(miner_address):
        miner_address = Address(seed=miner_address).address
    
    db_connection = get_db_connection(opt, port)

    # Start the node with tracker services and the new transaction services
    # as well as the mining process
    start(opt, remaining, host, port, active_peers,
          TransactionSynchronizer(db_connection, miner_address))
