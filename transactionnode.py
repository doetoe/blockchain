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
from flask import request
from node import node, start, node_address, active_peers, \
    get_nodedata_dir, helptext, get_host_port
from transaction import Transaction
from config import BLOCKCHAIN_CLASS # should always be TransactionBlockChain or a subclass

db_connection = None # sqlite3.connect("")
local_blockchain = BLOCKCHAIN_CLASS()

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
    update_blockchain()
    return json.dumps(
        list(transaction.__dict__
             for transaction in get_unprocessed(db_connection)))

def update_db_from_blockchain():
    """Resets the block ID for each transaction in the mempool database"""
    db_connection.execute(
        "update transactions set block = NULL")
    for block in local_blockchain:
        for tx in block.get_transaction_bundle():
            # Don't do anything with transactions in the blockchain that
            # are not in the mempool 
            db_connection.execute(
                "update transactions set block = ? where uuid = ?",
                (block.index, tx.uuid))
    db_connection.commit()

def update_blockchain():
    """Update the locally stored version of the blockchain by querying the nodes
    and update the database from it."""
    # download/update blockchain
    # update_peers(node_address, active_peers) # -> not necessary
    longest_blockchain = get_longest_blockchain(
        local_blockchain, node_address, active_peers)
    # update transaction pool (database): mark/unmark blocks
    # Note that all existing transactions should in theory be in this database.
    # Could assume that the database is up to date w.r.t. the old blockchain and
    # only update for the newer blocks (on starting the mempool the validity will
    # be initialized from the blockchain)
    if not local_blockchain is longest_blockchain:
        local_blockchain = longest_blockchain
        update_db_from_blockchain()

@node.route('/balance', methods=['GET'])
def balance():
    # Note: block rewards and recipients of fees don't end up in the database
    update_blockchain()
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

# TODO: check this function
@node.route('/confirmations', methods=['GET'])
def confirmations():
    update_blockchain()
    uuid = request.args.get('transaction_id', "")
    if uuid == "":
        abort(400)
    block = db_connection.execute(
        "select block from transactions where uuid=?;",
        (uuid,)).fetchone()[0]
    if block is None:
        return "0"
    else:
        return str(len(local_blockchain) - block)

def get_database_dir(port, create=False):
    return get_nodedata_dir(port, "", create)

def transaction_helptext(filename):
    return helptext(filename) + \
        "-d <db>       transaction database (default transactions.db)"

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
    

if __name__ == '__main__':
    # options for transaction database. Take care of the unicity of filenames
    # for different nodes.
    opt, remaining = getopt.getopt(sys.argv[1:], "hHp:t:d:")
    opt = dict(opt)
    if "-h" in opt:
        print(transaction_helptext(os.path.basename(sys.argv[0])))
        sys.exit()

    host, port = get_host_port(opt)
    node_address = "%s:%d" % (host,port)
        
    local_blockchain = BLOCKCHAIN_CLASS()
    db_connection = get_db_connection(opt, port)

    # Start the node with tracker services and the new transaction services
    # as well as the mining process
    start(opt, remaining, host, port, node_address, active_peers)
