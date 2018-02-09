#! /usr/bin/env python3

from flask import Flask, request
import os
import json
import sys
import time
import getopt

from config import DIFFICULTY, LEASE_TIME

tracker = Flask(__name__)
tracker.registered_peers = {}

@tracker.route('/peers', methods=['GET'])
def peers():
    """
    Returns a list of registered peers. 
    At this time they are simply identified by the 
    presence of a subdirectory whose name is the port number, and what is 
    returned are the port numbers as a list of strings.
    It will also get rid of peers whose lease time has passed (rather than
    have that done in a separate thread).
    """
    now = time.time()
    tracker.registered_peers = \
        dict(peer for peer in tracker.registered_peers.items() if
             now - peer[1] < LEASE_TIME)
    return json.dumps(list(tracker.registered_peers.keys()))

@tracker.route('/difficulty', methods=['GET'])
def difficulty():
    """This should not really come from the tracker. It only depends on the
    blockchain."""
    return str(DIFFICULTY)

@tracker.route('/register', methods=['GET'])
def register():
    tracker.registered_peers[request.args.get('url')] = time.time()
    
@tracker.route('/unregister', methods=['GET'])
def unregister():
    peer = request.args.get('url')
    if peer in tracker.registered_peers:
        tracker.registered_peers.pop(peer)
    
if __name__ == '__main__':
    args, remaining = getopt.getopt(sys.argv[1:], "H:p:h")
    args = dict(args)
    if "-h" in args:
        print("""Usage: 
        %s [options]

        Options:
        -h          show this help
        -H <host>   the host on which to run (default 127.0.0.1)
        -p <port>   the port on which to listen (default 5000)

        Note that when host or port are set, the nodes must be informed, by setting the
        right TRACKER_URL in config.py.
        """ % (os.path.basename(sys.argv[0])))
        sys.exit()
    host = args.get("-H", "127.0.0.1")
    port = int(args.get("-p", 5000))
    tracker.run(host=host, port=port)
