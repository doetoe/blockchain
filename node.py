#! /usr/bin/env python3

"""
When this is run as a script, it will try to connect to a tracker, which is
just any other node that serves as a tracker for more nodes, and
exit if it cannot. Otherwise it will start mining, while synchronizing 
with other nodes. 
In parallel it runs an http server that operates a full node:

/blockchain    - returns the current blockchain in json format
/chainlength   - returns the length of the chain of this miner
/block?index=n - returns block n in json format, or 400 if doesn't exist

provides tracking services:

/nodes         - return a list of registered nodes

and 

/running       - returns "running" if accessible

"""

from blockchain import BlockChain
from config import DIFFICULTY, CHAINDATA_DIR, TRACKER_ADDRESSES, BLOCKCHAIN_CLASS
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
node.active_peers = {}

def timeout_peers():
    """Remove stale peers from the list of active peers"""
    node.active_peers = \
        dict(peer for peer in node.active_peers.items() if
             now - peer[1] < LEASE_TIME)

@node.route('/nodes', methods=['GET'])
def nodes():
    """
    Returns a list of known nodes in the form of a json list of complete
    internet URL's (without protocol specifier), e.g. hostname.com:5001. 
    It will also get rid of nodes whose lease time has passed (rather than
    have that done in a separate thread).
    Note: in reality it returns a list with the strings which clients called
    /register with. Nodes expect these to be URL's.
    """
    now = time.time()
    timeout_peers()
    return json.dumps(list(node.active_peers.keys()))

# @node.route('/difficulty', methods=['GET'])
# def difficulty():
#     """This should not really come from the node. It only depends on the
#     blockchain."""
#     return str(DIFFICULTY)

@node.route('/register', methods=['GET'])
def register():
    node.active_peers[request.args.get('url')] = time.time()
    
# @node.route('/unregister', methods=['GET'])
# def unregister():
#     peer = request.args.get('url')
#     if peer in node.active_peers:
#         node.active_peers.pop(peer)

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
    ret = BLOCKCHAIN_CLASS.load(data_dir).as_json()
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
    """Returns whether a node is running at this address."""
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

def update_peers(address):
    """Update status of peers known to the specified address within this node,
    including the address itself.
    Since the peers are expected to keep their list of known peers up-to-date,
    this won't be recursed.
    """
    if not running(address):
        if address in node.active_peers:
            node.active_peers.pop(address)
        return

    now = time.time()
    node.active_peers[address] = now
    
    try:
        peers = requests.get("http://%s/nodes" % address).json()
    except requests.ConnectionError:
        return
    for peer in peers:
        if running(peer):
            node.active_peers[peer] = now
        elif peer in node.active_peers:
            node.active_peers.pop(peer)
        
def start_mining(host, port, shared_dict):
    """This is the main function, that executes in an infinite loop as long
    as this node is running."""
    chaindata_dir = os.path.join(CHAINDATA_DIR, str(port))
    if not os.path.isdir(CHAINDATA_DIR):
        os.mkdir(CHAINDATA_DIR)
    if not os.path.isdir(chaindata_dir):
        os.mkdir(chaindata_dir)
    blockchain = BLOCKCHAIN_CLASS.load(data_dir=chaindata_dir)
    assert blockchain.is_valid(DIFFICULTY)

    url = "%s:%d" % (host, port)
    while shared_dict["running"]: # stop mining when webserver is stopped
        # update registration in every iteration
        # If you only want to broadcast updated blocks, you could do this
        # when you find a block.
        update_peers()
        for peer_url in node.active_peers.keys():
            try:
                requests.get("%s/register" % peer_url, params={"url": url})
            except requests.ConnectionError:
                print("Couldn't register with %s" % peer_url)
        print("Chain length = %d" % len(blockchain))
        updated = False # to avoid unnecessary disk operations
        for node_url in node.active_peers.keys():
            if node_url == url: # the current node itself
                continue
            try:
                if chainlength(node_url) > len(blockchain):
                    node_blockchain = BLOCKCHAIN_CLASS.from_url(
                        "http://%s/blockchain" % (node_url))
                    if node_blockchain.is_valid(DIFFICULTY) and \
                       len(node_blockchain) > len(blockchain):
                        blockchain = node_blockchain
                        updated = True
            except requests.ConnectionError:
                pass
        if updated:
            blockchain.save(chaindata_dir)
        nextblock = blockchain.mine(DIFFICULTY, intents=1000)
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
        -p <port>     the port on which to listen (default the first available one starting at 5000)
        -t <address>  a peer (tracker) address, by default a hardcoded list will be tried
        """ % (os.path.basename(sys.argv[0]), TRACKER_ADDRESSES))
        sys.exit()
    
    host = opt.get("-H", "127.0.0.1")

    if "-p" in opt:
        port = int(opt["-p"])
        if not port_is_free(port):
            raise RuntimeError("Port %d is already in use" % port)
    else: 
        # look for free port
        port = 5000
        while not port_is_free(port):
            port += 1

    if "-t" in opt:
        update_peers(opt["-t"])
    if not node.active_peers: # either tracker not running or not specified
        for address in TRACKER_ADDRESSES:
            update_peers(address)
    if not node.active_peers:
        print("No active nodes found. Going solo.")

    # This generates a dictionary that can be shared between processes
    shared_dict = Manager().dict()
    shared_dict["running"] = True

    miner = Process(
        target=start_mining,
        args=(host, port, shared_dict))
    miner.start()
    
    print ("running node on %s:%d" % (host,port))
    try:
        node.run(host=host, port=port)
    except:
        shared_dict["running"] = False

