#! /usr/bin/env python3

from block import Block
from blockchain import BlockChain
from config import CHAINDATA_DIR, TRACKER_ADDRESS
from util import port_is_free
from flask import Flask, request, abort
import requests
import os
import json
import sys
import time
import getopt
from multiprocessing import Process, Manager

node = Flask(__name__)

"""
When this is run as a script, it will try to connect to the tracker, and
exit if it cannot. Otherwise it will start mining, while synchronizing 
with other nodes. 
In parallel it runs an http server that serves

/running       - returns "running" if accessible
/blockchain    - returns the current blockchain in json format
/chainlength   - returns the length of the chain of this miner
/block?index=n - returns block n in json format, or 400 if doesn't exist
"""

@node.route('/running', methods=['GET'])
def running():
    return "running"
    
@node.route('/blockchain', methods=['GET'])
def blockchain():
    """
    Loads the blockchain from disk and serves it as a json list of dictionaries.
    """
    port = request.environ["SERVER_PORT"] # already is a string
    data_dir = os.path.join(CHAINDATA_DIR, port)
    ret = BlockChain.load(data_dir).as_json()
    return ret

@node.route('/chainlength', methods=['GET'])
def chainlength():
    """Note that the indexing starts at 0, so if the length is n, the next
    block to mine is block n."""
    port = request.environ["SERVER_PORT"]
    data_dir = os.path.join(CHAINDATA_DIR, port)
    return str(len(os.listdir(data_dir)))
    
@node.route('/block', methods=['GET'])
def block():
    """
    Loads the specified block from disk and serves it as a json dictionary.
    """
    # trick to inspect request:
    # def unknown_type_handler(x):
    #     if not isinstance(x, int) and not isinstance(x, str):
    #         return "***"
    #     else:
    #         raise TypeError
    # return json.dumps(request.__dict__, default=unknown_type_handler)
    index = int(request.args.get('index'))
    # find out what port you are running on: that is the directory name
    port = request.environ["SERVER_PORT"]
    filename = os.path.join(CHAINDATA_DIR, port, "%06d.json" % index)
    if not os.path.isfile(filename):
        abort(400)
    with open(filename, 'r') as block_file:
        return block_file.read()

def running(url):
    address = "http://%s/running" % url
    try:
        return requests.get(address).text == "running"
    except:
        return False

def chainlength(url):
    address = "http://%s/chainlength" % url
    try:
        return int(requests.get(address).text)
    except:
        return -1
    
def start_mining(host, port, difficulty, tracker_url, shared_dict):
    chaindata_dir = os.path.join(CHAINDATA_DIR, str(port))
    if not os.path.isdir(CHAINDATA_DIR):
        os.mkdir(CHAINDATA_DIR)
    if not os.path.isdir(chaindata_dir):
        os.mkdir(chaindata_dir)
    blockchain = BlockChain.load(data_dir=chaindata_dir)
    assert blockchain.is_valid(difficulty)

    url = "%s:%d" % (host, port)
    while shared_dict["running"]: # stop mining when webserver is stopped
        # update registration in every iteration
        # If you only want to broadcast updated blocks, you could do this
        # when you find a block.
        try:
            requests.get("%s/register" % tracker_url, params={"url": url})
        except requests.ConnectionError:
            print("Couldn't connect to tracker: mining local blockchain")
            # Could also abort here, since unbroadcasted blocks won't
            # get validated
        print("Chain length = %d" % len(blockchain))
        try:
            nodes = [url for url in
                     requests.get("%s/nodes" % tracker_url).json()
                     if running(url)]
            # print(nodes)
        except requests.ConnectionError:
            nodes = []
        updated = False # to avoid unnecessary disk operations
        for node_url in nodes:
            if node_url == url: # the current node itself
                continue
            try:
                if chainlength(node_url) > len(blockchain):
                    node_blockchain = BlockChain.from_url(
                        "http://%s/blockchain" % (node_url))
                    if node_blockchain.is_valid(difficulty) and \
                       len(node_blockchain) > len(blockchain):
                        blockchain = node_blockchain
                        updated = True
            except requests.ConnectionError:
                pass
        if updated:
            blockchain.save(chaindata_dir)
        nextblock = blockchain.mine(difficulty, intents=1000)
        if nextblock is not None:
            blockchain.append(nextblock)
            blockchain.save(chaindata_dir)
            print("New block found: %s" % nextblock)
    # This shouldn't be public, otherwise you could eliminate other nodes
    # requests.get("%s/unregister" % tracker_url, params={"url", str(port)})
    print("exiting")
            
# Run mining node at specified port, or, if no port is specified, look for
# port that is free, probably one that has run before if available.
# It will at the same time start mining and start broadcasting.
if __name__ == '__main__':
    opt, remaining = getopt.getopt(sys.argv[1:], "H:p:ht:")
    opt = dict(opt)
    if "-h" in opt:
        print("""Usage: 
        %s [options]

        Options:
        -h            show this help
        -H <host>     the host on which to run (default 127.0.0.1)
        -p <port>     the port on which to listen (default the first available one after 5000)
        -t <address>  the tracker address, default %s
        """ % (os.path.basename(sys.argv[0]), TRACKER_ADDRESS))
        sys.exit()
    
    host = opt.get("-H", "127.0.0.1")
    tracker_url = "http://%s" % (opt.get("-t", TRACKER_ADDRESS))
    
    if "-p" in opt:
        port = int(opt["-p"])
        if not port_is_free(port):
            raise RuntimeError("Port %d is already in use" % port)
    else: 
        # look for free port
        port = 5001
        while not port_is_free(port):
            port += 1

    try:
        difficulty = int(requests.get("%s/difficulty" % tracker_url).text)
    except BaseException as e:
        raise ConnectionError(
            "Tracker not running at %s: %s. Set the correct location in config.py" \
            % (tracker_url, type(e)) + \
            "or pass it on the command line.")

    # This generates a dictionary that can be shared between processes
    shared_dict = Manager().dict()
    shared_dict["running"] = True

    miner = Process(target=start_mining, args=(host, port, difficulty, tracker_url, shared_dict))
    miner.start()
    
    print ("running node on port %d" % port)
    try:
        node.run(host=host, port=port)
    except:
        shared_dict["running"] = False

