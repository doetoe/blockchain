#! /usr/bin/env python3

import sys
import getopt
import os
import requests
from address import Address, could_be_valid_address
from transaction import Transaction
from config import MEMPOOL_ADDRESS

def showhelp(path):
    print("""Usage:
        {0} <cmd> [options] [args]

        where <cmd> can be:

        - help   
          Show this help
          
        - send <amount> <address>

          Options:
          -s <seed>      the seed from which the address is deterministically generated
          -f <file>      the file from which the Address object can be read
                         Either seed or file must be specified.
          -M <msg>       a message to include in the transaction. 
          -F <fee>       optional transaction fee.

          A transaction for the specified amount is created and sent to the specified
          address. If instead of an address a seed is passed for the generation of an
          address, the address will be generated. If you pass a seed, make sure that
          it doesn't have the form resembling a valid address (namely a hex string of
          length 96).
        
        - address <seed>

          print the (public) address associated to the seed

    """.format(os.path.basename(path), MEMPOOL_ADDRESS))

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help" or sys.argv[1] == "-h":
        showhelp(sys.argv[0])
        sys.exit()
        
    cmd = sys.argv[1]
    
    if cmd == "send":
        opt, remaining = getopt.getopt(sys.argv[2:], "s:f:H:M:F:")
        opt = dict(opt)
        s,f = "-s" in opt, "-f" in opt
        assert len(remaining) == 2, "two arguments required: amount and address"
        assert s and not f or f and not s, \
            "Have to specify either a seed or an address file and not both"
        amount = float(remaining[0])
        dest = remaining[1]
        if not could_be_valid_address(dest):
            dest = Address(seed=dest).address
        mempool_address = opt.get("-t", MEMPOOL_ADDRESS)
        if "-s" in opt:
            address = Address(seed=opt["-s"])
        else:
            address = Address.load(opt["-f"])
        msg = opt.get("-M", "")
        fee = opt.get("-F", 0)
        tx = Transaction(address.address, dest, amount, fee, msg)
        tx.sign(address)
        mempool_url = "http://%s" % (mempool_address)
        try:
            requests.put("%s/pushtx" % mempool_url, json=tx.as_json())
            print("Submitted:")
            print(tx)
        except requests.ConnectionError as e:
            print("Couldn't submit transaction: %s" % e)
    elif cmd == "address":
        opt, remaining = getopt.getopt(sys.argv[2:], "")
        print(Address(seed=remaining[0]).address)
    else:
        print("Command '%s' not recognized" % cmd)
        sys.exit()
