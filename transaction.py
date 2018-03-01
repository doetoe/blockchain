#! /usr/bin/env python3

import json
from textwrap import dedent
import requests
import uuid as uuid_module
from address import verify_signature
from collections import defaultdict
from block import Block
from blockchain import BlockChain
from config import BLOCK_REWARD, MAX_TRANSACTIONS_PER_BLOCK, NEW_ADDRESS_BALANCE

class Transaction(object):
    """
    from_addr and to_addr are public addresses. Amount and fee are floats.
    The message is any string, and the signature is the concatenation
    of from_addr, to_addr, amount, fee, msg, encrypted with the private key
    associated to the "from_addr" address.

    Only pass a uuid if this is a copy of an existing transaction, otherwise
    a new uuid will be automatically created.

    >>> from address import Address
    >>> addr1 = Address()
    >>> addr2 = Address()
    >>> tx = Transaction(addr1.address, addr2.address, 1.0, 0.01, "Test")
    >>> tx.sign(addr1)
    >>> print(Transaction.from_json(tx.as_json()))
    id: ...
    amount: ...
    signature: ...

    >>> tx.is_valid()
    True

    >>> tx2 = Transaction(addr2.address, addr1.address, 0.5, 0.0, "Test2")
    >>> tx2.is_valid()
    False
    >>> tx2.sign(addr1) # not the sender!
    >>> tx2.is_valid()
    False

    >>> bundle = TransactionBundle(msg="A bundle of two transactions",
    ...                            transactions=[tx, tx2])
    >>> bundle = TransactionBundle.from_json(bundle.as_json())
    >>> print(bundle.msg)
    A bundle of two transactions
    >>> for tx in bundle:
    ...     print(tx.msg)
    Test
    Test2
    """
    def __init__(self, from_addr, to_addr, amount,
                 fee=0, msg="", signature=None, uuid=None):
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.amount = amount
        self.fee = fee
        self.msg = msg
        # These should usually not be set
        self.signature = signature
        self.uuid = uuid or uuid_module.uuid4().hex # random 32 hex string

    def sign(self, address):
        """Sign the block with the specified Address. If you don't trust this
        function, you can directly set self.signature to the signed version of
        self.header()."""
        self.signature = address.sign(self.header())

    def is_valid(self):
        """Check that the signature is equal to the string representation
        of the transaction encrypted with the private key associated to
        the from address."""
        return self.signature is not None and \
            verify_signature(self.header(), self.signature, self.from_addr)
    
    @staticmethod
    def from_json(s):
        print(s)
        return Transaction(**json.loads(s))
    
    def as_json(self):
        return json.dumps(self.__dict__)

    def header(self):
        return ("{0.uuid}:{0.from_addr}:{0.to_addr}:" 
                + "{0.amount}:{0.fee}:{0.msg}").format(self)
            
    def __str__(self):
        return dedent("""\
            id:        {0.uuid}
            amount:    {0.amount}
            from:      {0.from_addr}
            to:        {0.to_addr}
            fee:       {0.fee}
            msg:       {0.msg}
            signature: {0.signature}""".format(self))    
    
class TransactionBundle(object):
    """A package of transactions that can be stored in the data field 
    of a Block."""
    def __init__(self, msg="", miner_address="", transactions=None):
        """msg is a free text field, miner_address is an address where the
        block reward and the fees should go to.
        The rest are the transactions themselves."""
        self.msg = msg
        self.miner_address = miner_address
        assert transactions is None or isinstance(transactions, list)
        self.transactions = transactions or []

    # def get_balance(self, address):
    #     """The change in the balance of the specified address due to transactions
    #     in this block."""
    #     raise NotImplementedError()
    
    @staticmethod
    def from_json(json_string):
        fields = json.loads(json_string)
        return TransactionBundle(
            msg=fields["msg"],
            miner_address=fields["miner_address"],
            transactions=[Transaction(**s)
                          for s in fields["transactions"]])

    def as_json(self):
        """This is a string that can be directly stored in the data field
        of a block."""
        return json.dumps(
            {"msg": self.msg,
             "miner_address": self.miner_address,
             "transactions": [tx.__dict__ for tx in self.transactions]})

    def is_valid(self):
        return all(tx.is_valid() for tx in self)
    
    def __len__(self):
        return len(self.blocks)

    def __iter__(self):
        return self.transactions.__iter__()

# # Special functions to treat a general block (with a generic data field) as a block
# # containing transactions.
# def get_transaction_bundle(block):
#     return TransactionBundle.from_json(block.data)
# 
# def get_balance(blockchain, address):
#     raise NotImplementedError()

class TransactionBlock(Block):
    def get_transaction_bundle(self):
        return TransactionBundle.from_json(self.data)
    
    def set_transaction_bundle(self, txs):
        self.data = txs.as_json()
        
    def is_valid(self):
        return super(TransactionBlock, self).is_valid() and \
            self.get_transaction_bundle().is_valid()

    
class TransactionBlockChain(BlockChain):
    @staticmethod
    def new_block(*args, **kwargs):
        """Contructs a block of a class compatible with this BlockChain class
        with the specified arguments"""
        return TransactionBlock(*args, **kwargs)
        
    def is_valid(self, difficulty):
        # check balances, validity and unicity of transactions
        try:
            # raises AssertionError if positivity of balances and unicity
            # of transactions is not satisfied
            self.get_balances()
        except AssertionError:
            return False
        return super(TransactionBlockChain, self).is_valid(difficulty)
    
    def get_balances(self, confirmations=1):
        """Returns a dictionary whose keys are all addresses appearing in the
        blockchain (including the miner_address), and whose values are the 
        balances.
        Actually a defaultdict that returns NEW_ADDRESS_BALANCE for new 
        addresses (this should be 0 for any serious use of course).
        If a number of confirmations is passed, the balance is based only on
        transactions that have the specified number of confirmations, default 1,
        meaning anywhere in the chain (last block or earlier)."""
        balances = defaultdict(lambda:NEW_ADDRESS_BALANCE)
        transaction_uuids = set()
        for block in self[:len(self) - confirmations + 1]:
            txs = block.get_transaction_bundle()
            for tx in txs:
                assert not tx.uuid in transaction_uuids, \
                    "Duplicate transaction in blockchain: %s" % tx.uuid
                transaction_uuids.add(tx.uuid)
                balances[tx.from_addr] -= (tx.fee + tx.amount)
                balances[tx.to_addr] += tx.amount
                balances[txs.miner_address] += (tx.fee + BLOCK_REWARD)
            assert all([balance >= 0 for balance in balances.values()]), \
                "Negative balances in block %d" % block.index
        return balances
    
    def get_balance(self, address, confirmations=0):
        return self.get_balances(confirmations)[address]

    # def mine(self, txs, difficulty, intents):
    #     # txs can be of any type and is obtained as the return value of
    #     # TransactionSynchronizer.next_block_data()
    #     # When this is a string, the superclass implementation is fine.
    #     raise NotImplementedError()
    
# execute doctest when executed as a script
# Displays output when passed -v or when a test fails
if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=
                    doctest.ELLIPSIS |
                    doctest.NORMALIZE_WHITESPACE |
                    doctest.IGNORE_EXCEPTION_DETAIL)
