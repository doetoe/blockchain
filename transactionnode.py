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
from flask import request
from node import node, start
from transaction import Transaction

# @node.route('/test', methods=['GET'])
# def test():
#     return "test"

@node.route('/pushtx', methods=['PUT'])
def pushtx():
    tx = Transaction.from_json(request.get_json())
    if not tx.is_valid():
        return "Invalid transaction; ignoring"
    if not exists(tx, node.transactions):
        insert(tx, node.transactions)
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
             for transaction in get_unprocessed(node.transactions)))

def update_db_from_blockchain():
    """Resets the block ID for each transaction in the mempool database"""
    node.transactions.execute(
        "update transactions set block = NULL")
    for block in node.blockchain:
        for tx in block.get_transaction_bundle():
            # Don't do anything with transactions in the blockchain that
            # are not in the mempool 
            node.transactions.execute(
                "update transactions set block = ? where uuid = ?",
                (block.index, tx.uuid))
    node.transactions.commit()

if __name__ == '__main__':
    # options for transaction database. Take care of the unicity of filenames
    # for different nodes.
    opt, remaining = getopt.getopt(sys.argv[1:], "hm:t:d:")
    opt = dict(opt)
    start(sys.argv, opt, remaining)
