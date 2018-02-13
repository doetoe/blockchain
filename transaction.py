#! /usr/bin/env python3

import json
from textwrap import dedent
import uuid as uuid_module
from address import verify_signature
import block

class Transaction(object):
    """
    from_addr and to_addr are public addresses. Signature and fee are floats. 
    The message is any string, and the signature is the concatenation
    of from_addr, to_addr, amount, fee, msg, encrypted with the private key
    associated to the "from_addr" address.

    Only pass a uuid if this is a copy of an existing transaction, otherwise
    a new uuid will be automatically created.

    >>> from address import Address
    >>> from_addr = Address()
    >>> to_addr = Address()
    >>> tx = Transaction(from_addr.address, to_addr.address, 1.0, 0.01, "Test")
    >>> tx.sign(from_addr)
    >>> print(Transaction.from_json(tx.as_json()))
    id: ...
    1.0
    from: Satoshi
    to:   Doetoe
    fee:  0.01
    Test
    signature: S.

    >>> print(tx.header())
    8f34b28ac96d48f1af0c05adfca9921d:Satoshi:Doetoe:1.0:0.01:Test

    >>> bundle = TransactionBundle(msg="A bundle of twice the same transaction",
    ...                            transactions=[tx, tx])
    >>> bundle = TransactionBundle.from_json(bundle.as_json())
    >>> print(bundle.msg)
    A bundle of twice the same transaction
    >>> for tx in bundle:
    ...     print(tx)
    id: 8f34b28ac96d48f1af0c05adfca9921d
    1.0
    from: Satoshi
    to:   Doetoe
    fee:  0.01
    Test
    signature: S.
    id: 8f34b28ac96d48f1af0c05adfca9921d
    1.0
    from: Satoshi
    to:   Doetoe
    fee:  0.01
    Test
    signature: S.
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
        return verify_signature(self.header(), self.signature, self.from_addr)
    
    @staticmethod
    def from_json(s):
        return Transaction(**json.loads(s))
    
    def as_json(self):
        return json.dumps(self.__dict__)

    def header(self):
        return ("{0.uuid}:{0.from_addr}:{0.to_addr}:" 
                + "{0.amount}:{0.fee}:{0.msg}").format(self)
            
    def __str__(self):
        return dedent("""\
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
            transactions=[Transaction(**s)
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

def get_transaction_bundle(block):
    return TransactionBundle.from_json(block.data)
    
# execute doctest when executed as a script
# Displays output when passed -v or when a test fails
if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=
                    doctest.ELLIPSIS |
                    doctest.NORMALIZE_WHITESPACE |
                    doctest.IGNORE_EXCEPTION_DETAIL)
