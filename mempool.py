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
import os
import json
import sys
import getopt
from transaction import Transaction
from blockchain import BlockChain

mempool = Flask(__name__)
mempool.transactions = {} # key: transaction, value: block index
mempool.blockchain = BlockChain()

@mempool.route('/pushtx', methods=['PUT'])
def pushtx():
    tx = Transaction.from_json(request.get_json())
    if not tx in mempool.transactions:
        mempool.transactions[tx] = None
        return "received transaction %s" % (tx.uuid)
    else:
        return "duplicate transaction; ignoring"
        
@mempool.route('/unprocessed', methods=['GET'])
def unprocessed():
    """
    Returns a list of unprocessed transactions in the form of a json list 
    of transaction contructor dictionaries. 
    """
    return json.dumps(list(transaction[0].__dict__
                           for transaction in mempool.transactions.items()
                           if transaction[1] is None))

# def running
# def chainlength
# tracker_url
# difficulty
# 
# def update_blockchain():  #### not needed: only update_transactions
#     # download/update blockchain
#     longest_blockchain = mempool.blockchain
#     try:
#         peers = [url for url in
#                  requests.get("%s/peers" % tracker_url).json()
#                  if running(url)]
#     except requests.ConnectionError:
#         peers = []
#     for peer_url in peers:
#         try:
#             if chainlength(peer_url) > len(longest_blockchain):
#                 peer_blockchain = BlockChain.from_url(
#                     "%s/blockchain" % (peer_url))
#                 if len(peer_blockchain) > len(longest_blockchain) and \
#                    peer_blockchain.is_valid(difficulty):
#                     longest_blockchain = peer_blockchain
#         except requests.ConnectionError:
#             pass
#     # update transaction pool
#     mempool.blockchain = longest_blockchain
# 
# # TODO
# @mempool.route('/balance', methods=['GET'])
# def balance():
#     update_blockchain()
#     address = request.args.get('address').text
#     return mempool.blockchain()
    
if __name__ == '__main__':
    args, remaining = getopt.getopt(sys.argv[1:], "H:p:h")
    args = dict(args)
    if "-h" in args:
        print("""Usage: 
        %s [options]

        Options:
        -h          show this help
        -H <host>   the host on which to run (default 127.0.0.1)
        -p <port>   the port on which to listen (default 5100)

        Note that when host or port are set, the users must be informed, 
        by setting the right MEMPOOL_URL in config.py or passing the URL
        on the command line.
        """ % (os.path.basename(sys.argv[0])))
        sys.exit()
    host = args.get("-H", "127.0.0.1")
    port = int(args.get("-p", 5100))
    mempool.run(host=host, port=port)
