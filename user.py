#! /usr/bin/env python3

import sys
import getopt
import os
import requests
from random import random, randrange
from util import multidict
from address import Address, could_be_valid_address
from transaction import Transaction
from config import NODE_ADDRESSES

def showhelp(path):
    print("""Usage:
        {0} <cmd> [options] [args]

        Some common options include:

          -t <address>   Address of a (known) tracker (node). May be repeated.
                         This will be added to a fixed list of possible nodes.

        where <cmd> can be:

        - help   
          Show this help
          
        - send <amount> <address>

          Options:
          -s <seed>      the seed from which the (sending) address is 
                         deterministically generated
          -f <file>      the file from which the Address object can be read
                         Either seed or file must be specified.
          -M <msg>       a message to include in the transaction. 
          -F <fee>       optional transaction fee.

          A transaction for the specified amount is created and sent to the 
          specified address. If instead of an address a seed is passed for the 
          generation of an address, the address will be generated. 
          The sender has to either specify an address with a seed or with a 
          keyfile. When you pass a seed, make sure that it doesn't have the 
          form resembling a valid address (namely a hex string of length 96).
        
        - address <seed>

          print the (public) address associated to the seed

        - balance [prefix]

          Show the balance of all addresses that start with the specified prefix. 
          All addresses if prefix is omitted.

        - rnd 

          -s <max-seed>  - generate seeds in the range 0..max-seed (default 100)
          -n <num>       - number of random transactions (default 1)

    """.format(os.path.basename(path), MEMPOOL_ADDRESS))

def send(tx, node_addresses):
    success = []
    for address in node_addresses:
        try:
            requests.put("http://%s/pushtx" % address, json=tx.as_json())
            success.append(address)
        except requests.ConnectionError as e:
            print("Couldn't submit transaction to %s" % (address))
    if success:
        print("Successfully submitted to %s" % (success))
        print(tx)

def get_node_addresses(opt):
    addresses = opt.get("-t", [])
    if not isinstance(addresses, list):
        addresses = [addresses]
    return addresses + NODE_ADDRESSES
        
if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help" or sys.argv[1] == "-h":
        showhelp(sys.argv[0])
        sys.exit()
        
    cmd = sys.argv[1]
    
    if cmd == "send":
        opt, remaining = getopt.getopt(sys.argv[2:], "s:f:M:F:t:")
        opt = multidict(opt)
        s,f = "-s" in opt, "-f" in opt
        assert len(remaining) == 2, "two arguments required: amount and address"
        assert s and not f or f and not s, \
            "Have to specify either a seed or an address file and not both"
        amount = float(remaining[0])
        dest = remaining[1]
        if not could_be_valid_address(dest):
            dest = Address(seed=dest).address
        if "-s" in opt:
            address = Address(seed=opt["-s"])
        else:
            address = Address.load(opt["-f"])
        msg = opt.get("-M", "")
        fee = opt.get("-F", 0)
        tx = Transaction(address.address, dest, amount, fee, msg)
        tx.sign(address)
        send(tx, get_node_addresses(opt))
    elif cmd == "address":
        opt, remaining = getopt.getopt(sys.argv[2:], "")
        opt = multidict(opt)
        print(Address(seed=remaining[0]).address)
    elif cmd == "balance":
        opt, remaining = getopt.getopt(sys.argv[2:], "t:")
        opt = multidict(opt)
        prefix = "" if not remaining else remaining[0]
        balances = None
        for node in get_node_addresses(opt):
            try:
                balances = requests.get("http://%s/balances" % node,
                                        params={"prefix": prefix}).json()
                break
            except requests.ConnectionError:
                continue
        if balances is None:
            print("Could not connect to any node")
        else:
            for balance in balances.items():
                print("%s: %.6f" % balance)
    elif cmd == "rnd":
        opt, remaining = getopt.getopt(sys.argv[2:], "n:s:t:")
        opt = multidict(opt)
        n = int(opt.get("-n", 1))
        max_seed = int(opt.get("-s", 100))
        for i in range(n):
            seed_from = str(randrange(max_seed))
            seed_to = str(randrange(max_seed))
            source = Address(seed=seed_from)
            dest = Address(seed=seed_to)
            amount = random()
            fee = amount * 0.1 * random()
            msg = "randomly generated transaction from seed %s to seed %s" \
                  % (seed_from, seed_to)
            tx = Transaction(source.address, dest.address, amount, fee, msg)
            tx.sign(source)
            send(tx, get_node_addresses(opt))
    else:
        print("Command '%s' not recognized" % cmd)
        sys.exit()
