from block import Block
import json
import os
import requests
import time
import glob
import datetime

class BlockChain(object):
    def __init__(self, blocks=None, data_dir=None, json_string=None):
        assert blocks is None or isinstance(blocks, list)
        self.blocks = blocks or []

    @staticmethod
    def load(data_dir):
        ret = BlockChain()
        if os.path.exists(data_dir):
            for filepath in glob.glob(os.path.join(data_dir, "*.json")):
                with open(filepath, 'r') as block_file:
                    block_info = json.load(block_file)
                    ret.append(Block(**block_info))
        ret.blocks.sort(key=lambda b: int(b.index))
        return ret
    
    # @staticmethod
    # def from_json(json_string):
    #     return BlockChain([Block(**s) for s in json.loads(json_string)])
        
    @staticmethod
    def from_url(url):
        """This function expects a url from which a json encoding a 
        blockchain will be returned."""
        chaindata = requests.get(url).json()
        return BlockChain([Block(**blockdata) for blockdata in chaindata])

    def as_json(self):
        return json.dumps([block.__dict__ for block in self.blocks])
    
    def is_valid(self, difficulty):
        """
        Is a valid blockchain if

        1) Each block is indexed one after the other
        2) Each block's prev hash is the hash of the prev block
        3) The block's hash is valid for the number of zeros

        Not taken into account but could be relevant:

        4) Conditions on the timestamps
        5) Difficulty depending on the timestamps of previous blocks
        """
        if not self.blocks:
            return True
        if self.blocks[0].index != 0:
            return False
        for (prev_block, block) in zip(self.blocks[:-1], self.blocks[1:]):
            if not block.satisfies_pow(difficulty):
                return False
            if not prev_block.is_valid_predecessor(block):
                return False
        return True
  
    def save(self, data_dir):
        """
        Save each block in this chain (the filename only depends on the index).
        """
        for block in self.blocks:
            block.save(data_dir)
  
    # def find_block_by_index(self, index):
    #     return self.blocks[index]
    # 
    # def find_block_by_hash(self, hash):
    #     for block in self.blocks:
    #         if b.get_hash() == hash:
    #             return block
    #     return None

    def head(self):
        return None if len(self) == 0 else self.blocks[-1]
      
    # def is_valid_extension(self, block):
    #     return True if not self.blocks else \
    #         self.head().is_valid_predecessor(block)

    def __len__(self):
        return len(self.blocks)

    def __eq__(self, other):
        return self.blocks == other.blocks

    def __ne__(self, other):
        return not self == other

    def mine(self, difficulty, intents=1000):
        """Try to mine a next block for the given difficulty by computing 
        the specified number of hashes.
        With the strategy used here the nonce is never very high, but that 
        doesn't matter. 
        The change in the timestamp in different calls will cause the hashes 
        to be different every time, even for the same nonces.
        If no valid block is found in the given number of intents, None is 
        returned.
        """
        index = 0 if len(self) == 0 else self.head().index + 1
        timestamp = datetime.datetime.utcnow().isoformat()
        data = "Block #%s" % (index)
        prev_hash = "" if len(self) == 0 else self.head().get_hash()
        block = Block(index=index, timestamp=timestamp,
                      data=data, prev_hash=prev_hash, nonce=0)
    
        for nonce in range(intents):
            block.nonce = nonce
            if block.satisfies_pow(difficulty):
                return block
            time.sleep(0.01)
        return None

    def append(self, block):
        """Extend the blockchain with a new block. It is not checked that 
        the blockchain is still valid"""
        self.blocks.append(block)
