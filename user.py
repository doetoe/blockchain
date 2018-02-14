#! /usr/bin/env python3

import sys
import getopt
import os
from address import Address

def showhelp(path):
    print("""Usage:
        {0} <cmd> [options] [args]

        where <cmd> can be:

        - help   
          Show this help
          
        - send <amount> <address>

          Options:
          -h          show this help
          -H <host>   the host on which to run (default 127.0.0.1)
          -p <port>   the port on which to listen (default 5100)

          
    """.format(os.path.basename(path)))


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        showhelp(sys.argv[0])
        sys.exit()
        
    cmd = sys.argv[1]
    

    opt, remaining = getopt.getopt(sys.argv[2:], "H:p:h")
    opt = dict(opt)
    if "-h" in opt:
        print("""Usage: 
        %s cmd [options]

        cmd:
          send      send 

        Options:
        -h          show this help
        -H <host>   the host on which to run (default 127.0.0.1)
        -p <port>   the port on which to listen (default 5100)

        Note that when host or port are set, the users must be informed, 
        by setting the right MEMPOOL_URL in config.py or passing the URL
        on the command line.
        """ % (os.path.basename(sys.argv[0])))
        sys.exit()
    
