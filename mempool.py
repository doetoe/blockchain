#! /usr/bin/env python3

"""This implements the global transaction mempool. This is a node that listens
for submitted transactions, and stores all of them indefinitely. It is now
assumed that there is only a single such node, there could be many that
synchronize.
It stores, validates and updates the full blockchain, and keeps track of
which block which transaction is in. On demand it can serve a list of
unprocessed transactions.

/pushtx(tx)       # or POST with several fields
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

mempool = Flask(__name__)
mempool.transactions = None # sqlite3.connect("")

# should be POST of several forms rather than a json?
@mempool.route('/pushtx', methods=['GET'])
def pushtx():
    mempool.transactions[
        Transaction.from_json(request.args.get('tx').json())] = None

@mempool.route('/unprocessed', methods=['GET'])
def unprocessed():
    """
    Returns a list of unprocessed transactions in the form of a json list 
    of transaction contructor dictionaries. 
    """
    return json.dumps(list(transaction[0].__dict__
                           for transaction in mempool.transactions
                           if transaction[1] is None))

@mempool.route('/balance', methods=['GET'])
def balance():
    address = request.args.get('tx').text
    return "to be implemented"
    
if __name__ == '__main__':
    opt, remaining = getopt.getopt(sys.argv[1:], "H:p:hd:")
    opt = dict(opt)
    if "-h" in opt:
        print("""Usage: 
        %s [options]

        Options:
        -h          show this help
        -H <host>   the host on which to run (default 127.0.0.1)
        -p <port>   the port on which to listen (default 5100)
        -d <db>     transaction database (default transactions.db)

        Note that when host or port are set, the users must be informed, 
        by setting the right MEMPOOL_URL in config.py or passing the URL
        on the command line.
        """ % (os.path.basename(sys.argv[0])))
        sys.exit()
    host = opt.get("-H", "127.0.0.1")
    port = int(opt.get("-p", 5100))
    db = opt.get("-d", "transactions.db")
    mempool.transactions = sqlite3.connect(db)
    mempool.run(host=host, port=port)
