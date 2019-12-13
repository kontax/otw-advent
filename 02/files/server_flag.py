#!/usr/bin/env python
import hexdump
import select
import signal
import socket
import sys
from time import sleep
import json
from io import BytesIO
from struct import pack, unpack
from traceback import print_exception


HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 4096   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

def num_convert(stream):
    shift = 0
    ret = 0
    is_negative = True
    while is_negative:
        num = get_int(stream, 1)
        ret |= ((num & 0x7f) << shift)
        shift += 7
        is_negative = num > 0x7f

    return twos_comp(ret, 64)


def num_unconvert(val):
    val = val % (1<<64)
    bitlen = len("{:0b}".format(val))
    output = []
    while bitlen >= 0:
        if bitlen >= 7:
            output.append((val & 0x7f) | 0x80)
        else:
            output.append(val & 0x7f)
        val >>= 7
        bitlen -= 7

    return bytes(output)

def get_int(stream_bytes, num):
    return int.from_bytes(stream_bytes.read(num), 'little')

def sz(b):
    return num_unconvert(len(b))

def sz_le(b):
    return pack('<H', len(b))

def login(username, password):
    x = b'\x0a' + sz(username) + username.encode() + \
        b'\x12' + sz(password) + password.encode()

    return b'\x12' + sz(x) + x

def attack(lvl):
    x = b'\x08' + num_unconvert(lvl)
    return b'\x1a' + sz(x) + x

def use(num=0):
    x = b'' if num == 0 \
            else b'\x18' + num_unconvert(num)
    return b'\x2a' + sz(x) + x

def item(direction, location, index):
    x = bytes([int(direction), int(location), 0x18, int(index)])
    return b'\x22' + sz(x) + x

def duplicate(location, index):
    x = bytes([0x08, int(location), 0x18, int(index), 0x10, int(location)])
    return b'\x22' + sz(x) + x

def buy_to_stash(index):
    x = b'\x08\x02\x18' + bytes([int(index)]) + b'\x10\x01'
    return b'\x22' + sz(x) + x

def sell_from_stash(index):
    x = b'\x08\x01\x18' + bytes([int(index)]) + b'\x10\x02'
    return b'\x22' + sz(x) + x

def send_command(sock, command_bytes, init):

    global KEY
    global CLI_IDX

    command_len = sz_le(command_bytes)

    print("\n----- Client -----")

    print(hexdump.hexdump(command_len))
    print(hexdump.hexdump(command_bytes))

    encoded = []
    for b in command_len + command_bytes:
        encoded.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
        CLI_IDX += 1

    sock.send(bytes(encoded))

def get_output(server, init):

    global BUFFER
    global KEY
    global SRV_IDX

    buf = server.recv(2)
    decoded_len = []
    for b in buf:
        decoded_len.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
        SRV_IDX += 1

    stream_length = unpack("<H", bytes(decoded_len))[0]
    SRV_IDX -= 2

    while len(buf) < (stream_length - 2):
        buf += server.recv(BUFFER)

    if len(buf) > 0:
        print("\n----- Server -----")

        decoded = []
        for b in buf:
            decoded.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
            SRV_IDX += 1

        print(hexdump.hexdump(bytes(decoded)))
    
    return decoded

# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))

not_logged_in = True
while not_logged_in:
    username = input("Username: ")
    password = input("Password: ")

    send_command(server, login(username, password), init)
    output = get_output(server, init)
    not_logged_in = 'msg' in output

# Fight 10 times to get 100 g
for i in range(10):
    print(f"Attack {i}")
    send_command(server, attack(3), init)
    send_command(server, use(), init)
    sleep(0.1)


# Buy an item from idx 1 for 5 rounds
for i in range(5):
    print(f"Buying {i}")
    send_command(server, buy_to_stash("1"), init)
    sleep(0.15)

    # Duplicate it 12 times
    for j in range(12):
        print(f"Duplicate {j}")
        send_command(server, duplicate("1", "0"), init)
        sleep(0.15)

    # Sell each one
    for j in range(13):
        print(f"Selling {j}")
        send_command(server, sell_from_stash("0"), init)
        sleep(0.15)

server.close()
print(f"Log in with {username} | {password} and buy the scroll")
