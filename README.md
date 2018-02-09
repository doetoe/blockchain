# README #

When tracker.py is executed as a script, it runs a (centralized) tracker that assists in peer discovery. 
To run a miner, execute node.py [port]

This will start mining and also connects to the tracker to discover other miners and synchronize with them.

Unless the tracker and all miners run on the same computer, you have to specify hostnames and ports, call both with -h to see options.

### What is this repository for? ###

* Implementing a toy blockchain to understand the concepts in some detail.
* Provide a base for experimentation.

### How do I get set up? ###

All this runs in Python 3, though probably Python 2 should work as well, possibly with some minor changes. It uses the non-standard module flask.

### Who do I talk to? ###

doetoe@protonmail.com

### Credits ###

The initial inspiration came from [ https://bigishdata.com/2017/10/17/write-your-own-blockchain-part-1-creating-storing-syncing-displaying-mining-and-proving-work/ ](this tutorial).