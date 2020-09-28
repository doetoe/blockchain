# README #

The lowest level system consists of a network of *nodes* that mindlessly mine data blocks satisfying a proof-of-work and forming a *blockchain*, and synchronize these among each other.

For this to work correctly you need the modules

* block
* blockchain
* node
* util
* config

The next level adds *transactions* to this. Users can generate private keys and addresses and send transactions to an additional kind of node called a *TransactionNode*. The totality of unprocessed transactions forms the *global transaction mempool*. Nodes can pull unprocessed transactions from it and include them in their blocks. For inclusion the nodes should check for additional validity: balances must be non-negative at any point in the blockchain.

For transactions to work correctly, you need the additional modules

* transaction
* address
* user
* transactionnode

The third level adds general purpose executable data to this (like smart contracts). This is still mostly to be done.

Communication happens through a HTTP-based REST-like API.

### Configuration ###

The local configuration is in `config.py`. It is a Python module that contains the following values:

* `DATA_DIR`         -- This is where all local data (locally known transactions, locally cached transaction database) are stored. When it is erased, no functionality is lost, only data, which will be reconstructed if they were known to the remained of the network.
* `NODE_ADDRESSES`   -- Some addresses to try to find peers. This list can be extended with command line arguments when running the node.
* `DIFFICULTY`       -- The number of leading zeros a hash must have to be considered to have satisfied a proof of work. At present this is not dynamically updated based on the network's processing power.
* `CONFIRMATIONS`    -- The number of blocks that should be mined after a block a transaction is contained in to be considered validated.
* `BLOCK_REWARD`     -- The number of coins awarded to the miner that creates a block.
* `MAX_TRANSACTIONS_PER_BLOCK`  -- The maximal number of transactions that can be included in a single block.
* `NEW_ADDRESS_BALANCE`  -- The amount that is automatically awarded to a new address. Since everybody can create an unlimited number of addresses, when not setting up a network for testing, the only sensible value is 0.

### Operation ###

##### Run node.py as a script. This runs a general node that assists in peer discovery and mining.

This will start mining and also tries to discover other nodes and synchronize with them. The URL of the node will be displayed.

The nodes operate a full node whose state can be queried through the commands
  
  * /running      - returns running when the node is running
  * /block(index) - returns block n in json format
  * /blockchain   - returns the blockchain as seen by this peer in json format
  * /chainlength  - returns the chainlength as seen by this peer

and they also peer discovery services through the commands

  * /nodes           - returns a list of URL's of registered miners
  * /register(url)   - register a url with the node

Unless the nodes run on the same computer, you have to specify hostnames and ports, call both with -h to see options.

Using the URL of the node, you can directly query the node with a web brower, e.g. `http://localhost:5000/block?index=1`

##### For transaction processing, run transactionnode.py rather than node.py.

These support the same functionality and network services as node.py nodes (of which they form a subclass), but additionally provide mempool services and transaction validation. New services are

* /pushtx(tx)       - put json describing a transaction
* /unprocessed      - json of all unprocessed transactions
* /balance(address) - the balance for this address. Optionally can specify the number confirmations you want using confirmations=<n>. 
		      1 means transactions anywhere in the blockchain, 0 means including unprocessed transactions.
* /balances(prefix) - like balance, but for all addresses with the given prefix. If prefix is omitted, all addresses.
* /confirmations(transaction_id)  - how many confirmations does the specified transaction have

##### Run user.py to use the network

All services can be directly accessed through HTTP, but this client makes it easier. It provides some additional functionality (like a minimal wallet/addressbook) as well.

* send              - send a transaction
* address           - see public address
* rnd               - to send random transactions to a node
* balance           - show balance(s)

The following are still to be implemented:

* create-address    - create an address and save it to a .pem file.

### Objectives ###

* To implement a simple but fully functional blockchain to understand the concepts in some detail.
* To provide a base for experimentation with variations and applications of blockchain technology.
* The networking part (peer discovery, block broadcasting, security of communications, etc) is not the main focus. 

### Dependencies ###

All this runs in Python 3, though Python 2 should work with some minor changes. It uses the non-standard modules `flask`, `ecdsa` and `dateutil`.

### Contact ###

doetoe@protonmail.com

### Credits ###
This is a greatly improved and extended version of what was initially loosely based on [this tutorial](https://bigishdata.com/2017/10/17/write-your-own-blockchain-part-1-creating-storing-syncing-displaying-mining-and-proving-work/).
