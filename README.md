# README #

When tracker.py is executed as a script, it runs a (centralized) tracker that assists in peer discovery. Its location should be set in config.py or otherwise hardcoded for the nodes (miners) to be able to access it. 
To run a miner, execute

node.py [port]

This will start mining and also connects to the tracker to discover other miners and synchronize with them. For the moment all miners have to run on the same computer, but that will be changed very soon.

### What is this repository for? ###

* Implementing a toy blockchain to understand the concepts in some detail.
* Provide a base for experimentation.
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

All this runs in Python 3, though probably Python 2 should work as well, possibly with some minor changes. It uses the non-standard module flask.

### Who do I talk to? ###

* doetoe@protonmail.com
