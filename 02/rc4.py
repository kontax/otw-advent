#!/usr/bin/env python

def KSA(key):
    keylength = len(key)

    S = list(range(256))

    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % keylength]) % 256
        S[i], S[j] = S[j], S[i]  # swap

    return S


def PRGA(S):
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]  # swap

        K = S[(S[i] + S[j]) % 256]
        yield K


def RC4(key):
    S = KSA(key)
    return PRGA(S)


if __name__ == '__main__':
    # test vectors are from http://en.wikipedia.org/wiki/RC4

    # ciphertext should be BBF316E8D940AF0AD3
    key = bytes.fromhex('95 2F 53 B6 F2 32 55 0B 0A 0D EE DD 8F 23 69 01')
    plaintext = bytes.fromhex('12 0E 0A 05 6C 61 6D 70 73 12 05 6C 61 6D 70 73')

    # ciphertext should be 1021BF0420
    #key = 'Wiki'
    #plaintext = 'pedia'

    # ciphertext should be 45A01F645FC35B383552544B9BF5
    #key = 'Secret'
    #plaintext = 'Attack at dawn'

    keystream = RC4(key)

    for c in plaintext:
        print("%02X" % (c ^ next(keystream)))
