#! /usr/bin/env python3

import json
from textwrap import dedent
import uuid

class Transaction(object):
    """
    from_addr and to_addr are public addresses. Signature and fee are floats. 
    The message is any string, and the signature is the concatenation
    of from_addr, to_addr, amount, fee, msg, encrypted with the private key
    associated to the "from_addr" address.
    Note that the signature

    >>> tx = Transaction("Satoshi", "Doetoe", 1.0, "S.", "0.01", "Test")
    >>> print(Transaction.from_json(tx.as_json()))

    >>> print(tx.header())

    >>> bundle = TransactionBundle(msg="A bundle of twice the same transaction",
    ...                            transactions=[tx, tx])
    >>> bundle = TransactionBundle.from_json(bundle.as_json())
    >>> print bundle.msg
    >>> for tx in bundle:
    ...     print tx
    """
    def __init__(self, from_addr, to_addr, amount, fee=0, msg=""):
        self.from_adr = from_addr
        self.to_addr = to_addr
        self.amount = amount
        self.fee = fee
        self.msg = msg
        self.signature = ""
        self.uuid = uuid.uuid4().hex # random 32 hex string

    def sign(self, signature):
        self.signature = signature

    def validate(self):
        """Check that the signature is equal to the string representation
        of the transaction encrypted with the private key associated to
        the from address."""
        return decrypt(self.header(), self.from_addr).startswith(self.uuid)
    
    @staticmethod
    def from_json(s):
        return Transaction(**json.loads(s))
    
    def as_json(self):
        return json.dumps(self.__dict__)

    def header(self):
        return "{0.uuid}:{0.from_addr}:{0.to_addr}:" \
            + "{0.amount}:{0.fee}:{0.msg}:".format(self)
            
    def __str__(self):
        return dedent("""
            id: {0.uuid}
            {0.amount}
            from: {0.from_addr}
            to:   {0.to_addr}
            fee:  {0.fee}
            {0.msg}
            signature: {0.signature}""".format(self))    
    
class TransactionBundle(object):
    """A package of transactions that can be stored in the data field 
    of a Block."""
    def __init__(self, msg="", transactions=None):
        self.msg = msg
        assert transactions is None or isinstance(transactions, list)
        self.transactions = transactions or []

    @staticmethod
    def from_json(json_string):
        fields = json.loads(json_string)
        return TransactionBundle(
            msg=fields["msg"],
            transactions=[Transaction(**json.loads(s))
                          for s in fields["transactions"]])

    def as_json(self):
        """This is a string that can be directly stored in the data field
        of a block."""
        return json.dumps(
            {"msg": self.msg,
             "transactions": [tx.__dict__ for tx in self.transactions]})

    def __len__(self):
        return len(self.blocks)

    def __iter__(self):
        return self.transactions.__iter__()
    
# execute doctest when executed as a script
# Displays output when passed -v or when a test fails
if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=
                    doctest.ELLIPSIS |
                    doctest.NORMALIZE_WHITESPACE |
                    doctest.IGNORE_EXCEPTION_DETAIL)