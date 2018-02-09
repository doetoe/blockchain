#! /usr/bin/env python3

from util import utc_to_local
import hashlib
import os
import json
import datetime
from textwrap import dedent

def to_string(index, prev_hash, data, timestamp, nonce):
    return "%d%s%s%s%s" % (index, prev_hash, data, timestamp, nonce)

def calculate_hash(index, prev_hash, data, timestamp, nonce):
    header_string = to_string(index, prev_hash, data, timestamp, nonce)
    sha = hashlib.sha256()
    sha.update(header_string.encode("utf8"))
    return sha.hexdigest()

class Block(object):
    def __init__(self, index, timestamp, prev_hash=None, hash=None,
                 data="", nonce=None):
        """
        Properties:

        index: 0,1,2,...
        timestamp: a UTC timestamp in isoformat (string)
        prev_hash: the hash of the previous block as a string
        data: string
        nonce: an arbitrary integer

        The data are such that block.__dict__ can be directly serialized to/
        deserialized from json format for interoperability with other languages.
        """
        self.index = index
        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.isoformat()
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.data = data
        self.nonce = nonce
        self.hash = hash

    def get_hash(self):
        """
        The sha256 hash of this object, that depends deterministically on the 
        fields index, timestamp, prev_hash, data, nonce
        """
        return calculate_hash(self.index, self.prev_hash, self.data,
                              self.timestamp, self.nonce)

    def save(self, data_dir):
        """Save a json version of this block to the specified directory"""
        filename = os.path.join(data_dir, "%06d.json" % (self.index))
        with open(filename, 'w') as block_file:
            json.dump(self.__dict__, block_file)

    def satisfies_pow(self, difficulty):
        """Check that the proof-of-work is satisfied for this block."""
        return self.get_hash().startswith('0' * difficulty)

    def is_valid_predecessor(self, next_block):
        """
        x.is_valid_predecessor(y) if y is a valid successor of x:

        - index is incremented by 1
        - y.prev_hash is the hash of x
        """
        return self.index + 1 == next_block.index and \
            self.get_hash() == next_block.prev_hash
    
    def __repr__(self):
        return "Block(index: %s, hash: %s)" % (self.index, self.get_hash())

    def pstring(self):
        """Returns a pretty string"""
        return dedent("""
            Block {0.index}
            - hash: {0.hash}
            - previous hash: {0.prev_hash}
            - nonce: {0.nonce}
            - timestamp: {1}
            Data:
            {0.data}
        """.format(self, utc_to_local(self.timestamp)))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
        # """It is assumed that the hash is sufficient to determine equality"""
        # return self.get_hash() == other.get_hash()

    # Not needed in Python 3: __ne__ will call __eq__ if not implemented. In Python 2:
    # def __ne__(self, other):
    #     return not self == other
