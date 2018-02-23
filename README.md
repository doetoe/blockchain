# README #

The lowest level system consists of a network of *nodes* that mindlessly mine data blocks satisfying a proof-of-work and forming a *blockchain*, and synchronize these among each other. Since the main focus of this exercise is not in the networking details (for the moment), like peer discovery, block broadcasting, etc, there is a *tracker* that allows nodes to find each other.

For this to works correctly you need the modules

* block
* blockchain
* tracker
* node
* util
* config

The next level adds *transactions* to this. Users can generate private keys and addresses and send transaction to an additional kind of node called a *mempool*, representing the *global transaction mempool*. Nodes can pull unprocessed transactions from it and include them in their blocks. Note that they are still the same blocks, the same mining, the same blockchains, only now the data field is interpreted as containing a bundle of transactions, which are executed when they get validated in the blockchain. For inclusion the nodes should check for additional validity: balances must be non-negative at any point in the blockchain.

For transactions to work correctly, you need the additional modules

* mempool
* transaction
* address
* user

and you should change the configuration file `config.py` to specify the correct blockchain class.

The third level adds general purpose executable data to this. This is still very much to be done and understood.

### Operation ###

##### Run tracker.py as a script. This runs a (centralized) tracker that assists in peer discovery. 

The tracker supports

* /running         - returns running when the tracker is running
* /nodes           - returns a list of URL's of registered miners
* /register(url)   - register a url with the tracker

##### For each miner you want to run, execute node.py as a script.

This will start mining and also connects to the tracker to discover other miners and synchronize with them.

The nodes support
  
  * /running      - returns running when the node is running
  * /block(n)     - returns block n in json format
  * /blockchain   - returns the blockchain as seen by this peer in json format
  * /chainlength  - returns the chainlength as seen by this peer

Unless the tracker and all miners run on the same computer, you have to specify hostnames and ports, call both with -h to see options.

##### For transaction management, additionally run mempool.py as a script

The mempool supports

* /pushtx(tx)       - put json describing a transaction
* /unprocessed      - json of all unprocessed transactions
* /balance(address) - the balance for this address. Optionally can specify the number confirmations you want using confirmations=<n>.
		      1 means transactions anywhere in the blockchain, 0 means including unprocessed transactions.
* /confirmations(transaction_id)  - how many confirmations does the specified transaction have
* run user.py as a script for each transaction you want to post.

### Objectives ###

* To implement a toy blockchain to understand the concepts in some detail.
* To provide a base for experimentation with variations and applications of blockchain technology.
* The networking part (peer discovery, block broadcasting, security of communications, etc) is not the main focus, so this just has a quick 'n' dirty design. 

### Dependencies ###

All this runs in Python 3, though Python 2 should work with some minor changes. It uses the non-standard modules flask, ecdsa and dateutil.

### Contact ###

doetoe@protonmail.com

### Credits ###

The initial inspiration came from [this tutorial](https://bigishdata.com/2017/10/17/write-your-own-blockchain-part-1-creating-storing-syncing-displaying-mining-and-proving-work/).
