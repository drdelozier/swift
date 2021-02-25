import hashlib
import os
import binascii


def encode_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    hash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    hash = binascii.hexlify(hash)
    hash = (salt + hash).decode('ascii')
    return hash


def verify_password(password, hash):
    salt = hash[:64].encode('ascii')
    old_hash = hash[64:]
    new_hash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    new_hash = binascii.hexlify(new_hash)
    new_hash = new_hash.decode('ascii')
    return old_hash == new_hash


def test_encode_password():
    hash = encode_password("mypassword")
    assert type(hash) is str
    assert len(hash) > 60


def test_verify_password():
    hash = encode_password("mypassword")
    result = verify_password("mypassword", hash)
    assert result, "Correct password does not verify"
    result = verify_password("xmypassword", hash)
    assert not result, "Incorrect password does improperly verify"
    result = verify_password("mypassxword", hash)
    assert not result, "Incorrect password does improperly verify"
    result = verify_password("mypasswordx", hash)
    assert not result, "Incorrect password does improperly verify"
    result = verify_password("mypassWord", hash)
    assert not result, "Incorrect password does improperly verify"
    result = verify_password("cat", hash)
    assert not result, "Incorrect password does improperly verify"


if __name__ == "__main__":
    test_encode_password()
    test_verify_password()
    print("Done.")
