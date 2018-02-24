from ecdsa import NIST192p as CURVE
from blockchain import BlockChain as BLOCKCHAIN_CLASS
# from transaction import TransactionBlockChain as BLOCKCHAIN_CLASS
CHAINDATA_DIR = 'chaindata'
TRACKER_ADDRESS = "localhost:5000"
MEMPOOL_ADDRESS = "localhost:5100"
DIFFICULTY = 3 # leading zeros
LEASE_TIME = 60 # how long the tracker keeps you registered in seconds
CONFIRMATIONS = 6 # number of confirmations before considering a transaction final
BLOCK_REWARD = 1
MAX_TRANSACTIONS_PER_BLOCK = 5
