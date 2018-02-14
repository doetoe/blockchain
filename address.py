#! /usr/bin/env python3

from ecdsa import SigningKey, VerifyingKey, NIST192p, BadSignatureError
from ecdsa.util import randrange_from_seed__trytryagain
import os
from config import CURVE
# from transaction import Transaction

# address and signature are in hex format
def verify_signature(msg, signature, address):
    verifying_key = VerifyingKey.from_string(bytes.fromhex(address), curve=CURVE)
    try:
        return verifying_key.verify(bytes.fromhex(signature), msg.encode("utf-8"))
    except BadSignatureError:
        return False

class Address(object):
    """
    >>> a = Address()
    >>> s = a.sign('hallo')
    >>> verify_signature('hallo', s, a.address)
    True
    >>> verify_signature('hello', s, a.address)
    False
    """
    def __init__(self, seed=None, signing_key=None):
        assert seed is None or signing_key is None
        if signing_key:
            self.signing_key = signing_key
        elif seed:
            secret_exp = randrange_from_seed__trytryagain(seed, CURVE.order)
            self.signing_key = SigningKey.from_secret_exponent(secret_exp, curve=CURVE)
        else:
            self.signing_key = SigningKey.generate(curve=CURVE)

        self.verifying_key = self.signing_key.get_verifying_key()
        # note that if instead of to_string() we would use to_der() 
        # or to_pem(), we could use different elliptic curves for different addresses
        self.address = self.verifying_key.to_string().hex()

    def sign(self, msg):
        return self.signing_key.sign(msg.encode("utf-8")).hex()

    # def sign(self, transaction):
    #     transaction.signature = self.sign_str(transaction.header())

    def save(self, filename):
        if not filename.endswith(".pem"):
            filename = "%s.pem" % filename
        with open(filename, 'w') as f:
            f.write(self.signing_key.to_pem())

    @staticmethod
    def load(filename):
        if not os.isfile(filename):
            filename = "%s.pem" % filename
        with open(filename) as f:
            signing_key = SigningKey.from_pem(f.read())
        return Address(signing_key=signing_key)

########################################################################
#
#   An encypting client
#
########################################################################

# from Crypto.PublicKey import RSA
# from Crypto.Signature import PKCS1_v1_5
# from Crypto.Hash import SHA
# # import pickle
# 
# class Address(object):
#     def __init__(self):
#         rng = Random.new().read
#         self.keypair = RSA.generate(1024, rng)
#         self.signer = PKCS1_v1_5.new(keypair)
#         self.publickey = self.keypair.publickey()
#         self.verifier = PKCS1_v1_5.new(self.publickey)
#         
#     @staticmethod
#     def text_hash(txt):
#         return SHA.new(txt.encode("utf-8"))
#         
#     def signature(self, txt):
#         return self.signer.sign(self.text_hash(txt))
# 
#     def verify(self, txt, signature):
#         return self.verifier.verify(self.text_hash(txt), signature)

# execute doctest when executed as a script
# Displays output when passed -v or when a test fails
if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=
                    doctest.ELLIPSIS |
                    doctest.NORMALIZE_WHITESPACE |
                    doctest.IGNORE_EXCEPTION_DETAIL)
