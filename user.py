from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
# import pickle

class Address(object):
    def __init__(self):
        rng = Random.new().read
        self.keypair = RSA.generate(1024, rng)
        self.signer = PKCS1_v1_5.new(keypair)
        # The public key is too long as an address. Is there a better
        # option? Use the address of bitcoin proper?
        # Some hash of the public key?
        self.publickey = self.keypair.publickey()
        self.verifier = PKCS1_v1_5.new(self.publickey)
        # self.address = SHA.new(pickle.dumps(self.publickey))
        
    @staticmethod
    def text_hash(txt):
        return SHA.new(txt.encode("utf-8"))
        
    def signature(self, txt):
        return self.signer.sign(self.text_hash(txt))

    def verify(self, txt, signature):
        return self.verifier.verify(self.text_hash(txt), signature)

    
