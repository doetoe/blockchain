#! /usr/bin/env python3

import unittest
from transaction import Transaction, TransactionBundle, \
    TransactionBlock, TransactionBlockChain
from address import Address
from config import NEW_ADDRESS_BALANCE

class TransactionBlockChainTest(unittest.TestCase):
    def test_new_balance(self):
        b = TransactionBlockChain()
        self.assertEqual(len(b.get_balances()), 0,
                         "No addresses in empty blockchain")
        self.assertEqual(b.get_balance(""), NEW_ADDRESS_BALANCE,
                         "Balance of unused address should be equal to" +
                         "the NEW_ADDRESS_BALANCE (%f)" % NEW_ADDRESS_BALANCE)
    
    def test_balances(self):
        # create some addresses
        keys = [Address(seed=str(i)) for i in range(5)]
        addr = [a.address for a in keys]
        tx01 = Transaction(addr[0], addr[1], 0.9, 0.01, "0 -> 1")
        tx01.sign(keys[0])
        self.assertTrue(tx01.is_valid())
        tx12 = Transaction(addr[1], addr[2], 0.2, 0   , "1 -> 2")
        self.assertFalse(tx12.is_valid())
        bundle0 = TransactionBundle(msg="0: -0.91, 1: +0.7, 2: +0.2, 3: +1.01",
                                    miner_address=addr[3],
                                    transactions=[tx01, tx12])
        self.assertFalse(bundle0.is_valid())
        
        block0 = TransactionBlock(0)
        block0.set_transaction_bundle(bundle0)
        self.assertFalse(block0.is_valid())
        tx12.sign(keys[1])
        self.assertTrue(tx12.is_valid())
        self.assertTrue(bundle0.is_valid())
        # The bundle isn't stored by reference, but in serialized form
        self.assertFalse(block0.is_valid())
        block0.set_transaction_bundle(bundle0)
        self.assertTrue(block0.is_valid())

        chain = TransactionBlockChain([block0])
        self.assertTrue(chain.is_valid(difficulty=0))
        self.assertFalse(chain.is_valid(difficulty=10))
        self.assertEqual(chain.balance(addr[0]), NEW_ADDRESS_BALANCE - 0.91)
        
        tx10 = Transaction(addr[1], addr[0], 1.5, 0.02, "1 -> 0")
        tx10.sign(keys[1])
        bundle1 = TransactionBundle(msg="0: +1.5, 1: -1.52, 2: +1.02",
                                    miner_address=addr[2],
                                    transactions=[tx10])

        block1 = TransactionBlock(1)
        block1.set_transaction_bundle(bundle1)

        chain.append(block1)
        self.assertTrue(chain.is_valid(difficulty=0))
        self.assertFalse(chain.is_valid(difficulty=10))
        self.assertEqual(chain.balance(addr[0]), NEW_ADDRESS_BALANCE - 0.91 + 1.5)
        self.assertEqual(chain.balance(addr[1]), NEW_ADDRESS_BALANCE + 0.7 - 1.52)

        for addr, balance in chain.get_balances():
            print("%s: %.4f" % (addr[:10], balance))
        
        self.assertFalse(
            TransactionBlockChain([block1, block0]).is_valid(difficulty=0))
        
if __name__ == '__main__':
    unittest.main()
