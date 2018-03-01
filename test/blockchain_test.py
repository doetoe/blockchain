#! /usr/bin/env python3

"""Script to execute all tests: unittests and doctests."""

# modules having doctests that can be run as a script to execute them
# unittest TestCases don't have to be imported when using "discover"
import sys
import os


import unittest, doctest

def suite(top_dir=None):
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import block
    import transaction
    import address

    # discovery is done from the directory where the main test
    # module (this one) is located
    testpath = os.path.dirname(os.path.realpath(__file__))
    
    # unittestsuites = [
    #    unittest.defaultTestLoader.loadTestsFromTestCase(test)
    #    for test in [TestCase1, ...]]
    unittestsuites = [unittest.defaultTestLoader.discover(
        testpath, pattern='test*.py', top_level_dir=top_dir)]

    doctests = [block, transaction, address]
    doctestsuites = [doctest.DocTestSuite(test, optionflags=
                                          doctest.ELLIPSIS |
                                          doctest.NORMALIZE_WHITESPACE |
                                          doctest.IGNORE_EXCEPTION_DETAIL)
                     for test in doctests]

    testsuites = unittestsuites + doctestsuites

    return unittest.TestSuite(testsuites)

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
