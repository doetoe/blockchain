# README #

When tracker.py is executed as a script, it runs a (centralized) tracker that assists in peer discovery. 
For each miner you want to run, execute node.py.

This will start mining and also connects to the tracker to discover other miners and synchronize with them.

Unless the tracker and all miners run on the same computer, you have to specify hostnames and ports, call both with -h to see options.

### Supported Web Services ###

The tracker supports

* /peers           - returns a list of URL's of registered miners
* /difficulty      - returns the present difficulty. In the future this should be a function
                     of the blockchain, not a centralized value.
* /register(url)   - register a url with the tracker

The nodes support

* /running      - returns running when the node is running
* /block(n)     - returns block n in json format
* /blockchain   - returns the blockchain as seen by this peer in json format
* /chainlength  - returns the chainlength as seen by this peer

### Objectives ###

* Implementing a toy blockchain to understand the concepts in some detail.
* Provide a base for experimentation with variations and applications.
* The networking part (peer discovery, block broadcasting, security of communications, etc) is not the main focus, so this just has a quick 'n' dirty design. 

### Dependencies ###

All this runs in Python 3, though probably Python 2 should work as well, possibly with some minor changes. It uses the non-standard modules flask, crypto and dateutil.

### Contact ###

doetoe@protonmail.com

### Credits ###

The initial inspiration came from [this tutorial](https://bigishdata.com/2017/10/17/write-your-own-blockchain-part-1-creating-storing-syncing-displaying-mining-and-proving-work/).