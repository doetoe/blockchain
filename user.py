#! /usr/bin/env python3

import sys
import getopt
import os
import requests
from address import Address
from transaction import Transaction

def showhelp(path):
    print("""Usage:
        {0} <cmd> [options] [args]

        where <cmd> can be:

        - help   
          Show this help
          
        - send <amount> <address>

          Options:
          -s <seed>   the seed from which the address is deterministically generated
          -f <file>   the file from which the Address object can be read
                      Either seed or file must be specified.
          -H <host>   the host of the mempool node (default 127.0.0.1)
          -p <port>   the port of the mempool node (default 5100)
          -m <msg>    a message to include in the transaction. 
          -F <fee>    optional transaction fee.
    """.format(os.path.basename(path)))


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        showhelp(sys.argv[0])
        sys.exit()
        
    cmd = sys.argv[1]
    if cmd == "send":
        opt, remaining = getopt.getopt(sys.argv[2:], "s:f:H:p:m:F:")
        opt = dict(opt)
        s,f = "-s" in opt, "-f" in opt
        assert len(remaining) == 2, "two arguments required: amount and address"
        assert s and not f or f and not s, \
            "Have to specify either a seed or a file and not both"
        amount = float(remaining[0])
        dest = remaining[1]
        host = opt.get("-H", "127.0.0.1")
        port = int(opt.get("-p", 5100))
        if "-s" in opt:
            address = Address(seed=opt["-s"])
        else:
            address = Address.load(opt["-f"])
        msg = opt.get("-m", "")
        fee = opt.get("-F", 0)
        tx = Transaction(address.address, dest, amount, fee, msg)
        tx.sign(address)
        url = "http://%s:%d" % (host, port)
        requests.put("%s/pushtx" % url, json=tx.as_json())
