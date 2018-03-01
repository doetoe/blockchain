# README #

The lowest level system consists of a network of *nodes* that mindlessly mine data blocks satisfying a proof-of-work and forming a *blockchain*, and synchronize these among each other.

For this to works correctly you need the modules

* block
* blockchain
* node
* util
* config

The next level adds *transactions* to this. Users can generate private keys and addresses and send transaction to an additional kind of node called a *mempool*, representing the *global transaction mempool*. Nodes can pull unprocessed transactions from it and include them in their blocks. For inclusion the nodes should check for additional validity: balances must be non-negative at any point in the blockchain.

For transactions to work correctly, you need the additional modules

* transaction
* address
* user
* transactionnode

and you should change the configuration file `config.py` to specify the correct blockchain class.

The third level adds general purpose executable data to this. This is still very much to be done and understood.

### Operation ###

##### Run node.py as a script. This runs a general node that assists in peer discovery and mining.

This will start mining and also tries to discover other nodes and synchronize with them.

The nodes operate a full node:
  
  * /running      - returns running when the node is running
  * /block(n)     - returns block n in json format
  * /blockchain   - returns the blockchain as seen by this peer in json format
  * /chainlength  - returns the chainlength as seen by this peer

and also peer discovery services

  * /nodes           - returns a list of URL's of registered miners
  * /register(url)   - register a url with the tracker

Unless the nodes run on the same computer, you have to specify hostnames and ports, call both with -h to see options.

##### For transaction processing, run transactionnode.py rather than node.py.

These support the same functionality and network services as node.py nodes, but additionally provide mempool services and transaction validation. New services are

* /pushtx(tx)       - put json describing a transaction
* /unprocessed      - json of all unprocessed transactions
* /balance(address) - the balance for this address. Optionally can specify the number confirmations you want using confirmations=<n>. 
		      1 means transactions anywhere in the blockchain, 0 means including unprocessed transactions.
* /balances(prefix) - like balance, but for all addresses with the given prefix. If prefix is omitted, all addresses.
* /confirmations(transaction_id)  - how many confirmations does the specified transaction have

##### Run user.py to use the network

All services can be directly accessed through http, but this client makes it easier. It provides some additional functionality (as a minimal wallet/addressbook) as well.

* send              - send a transaction
* address           - see public address
* rnd               - to send random transactions to a node
* balance           - show balance(s)

The following are still to be implemented:

* create-address    - create an address and save it to a .pem file.

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
