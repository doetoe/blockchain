#! /usr/bin/env python3

from flask import Flask, request
import os
import json
import sys
import time
import getopt

from config import DIFFICULTY, LEASE_TIME, TRACKER_ADDRESS

tracker = Flask(__name__)
tracker.registered_nodes = {}

@tracker.route('/nodes', methods=['GET'])
def nodes():
    """
    Returns a list of registered nodes in the form of a json list of complete
    internet URL's (without protocol specifier), e.g. hostname.com:5001. 
    It will also get rid of nodes whose lease time has passed (rather than
    have that done in a separate thread).
    Note: in reality it returns a list with the strings which clients called
    /register with. Nodes expect these to be URL's.
    """
    now = time.time()
    tracker.registered_nodes = \
        dict(node for node in tracker.registered_nodes.items() if
             now - node[1] < LEASE_TIME)
    return json.dumps(list(tracker.registered_nodes.keys()))

@tracker.route('/difficulty', methods=['GET'])
def difficulty():
    """This should not really come from the tracker. It only depends on the
    blockchain."""
    return str(DIFFICULTY)

@tracker.route('/register', methods=['GET'])
def register():
    tracker.registered_nodes[request.args.get('url')] = time.time()
    
# @tracker.route('/unregister', methods=['GET'])
# def unregister():
#     node = request.args.get('url')
#     if node in tracker.registered_nodes:
#         tracker.registered_nodes.pop(node)
    
if __name__ == '__main__':
    args, remaining = getopt.getopt(sys.argv[1:], "t:h")
    args = dict(args)
    if "-h" in args:
        print("""Usage: 
        %s [options]

        Options:
        -h             show this help
        -t <address>   the address on which to run (default %s)

        Note that when host or port are set, the nodes must be informed, 
        by setting the right TRACKER_ADDRESS in config.py or passing the URL 
        on the command line.
        """ % (os.path.basename(sys.argv[0]), TRACKER_ADDRESS))
        sys.exit()
    address = args.get("-t", TRACKER_ADDRESS).split(":")
    host, port = address[0], 80 if len(address) == 1 else int(address[1])
    tracker.run(host=host, port=port)
