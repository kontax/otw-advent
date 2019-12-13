#!/usr/bin/env python
import hexdump
import select
import socket
import struct

HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 1024   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

def decode(data, init):
    global CLI_IDX
    global KEY
    decoded = []
    for b in data:
        decoded.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
        CLI_IDX += 1
    
    return hexdump.hexdump(bytes(decoded))

def encode(data, init):
    global SRV_IDX
    global KEY
    encoded = []
    for b in data:
        encoded.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
        SRV_IDX += 1

    return bytes(encoded)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")

# Wait for user to input
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")
#input("Press any key when complete...")


# Connect to the real server and get the initial response
init = bytes.fromhex('C0 84 2F D3 23 41 11 D4  B5 BD 4C 88 29 39 6F 4F')
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

# Get login data
print("\n----- Client -----")
print(decode(client.recv(2), init))
print(decode(client.recv(BUFFER), init))

# Send initial data
with open('fakefiles/init', 'r') as f:
    initialize = bytes.fromhex(f.read().replace('\n', ' '))

    print("\n----- Server -----")
    print(hexdump.hexdump(initialize))
    client.send(encode(struct.pack("<H", len(initialize)), init))
    client.send(encode(initialize, init))


while True:
    print(decode(client.recv(2), init))
    print(decode(client.recv(BUFFER), init))

    #input("Send bytes? ")
    with open('fakefiles/send', 'r') as f:
        data_to_send = bytes.fromhex(f.read().replace('\n', ' '))

    print("\n----- Server -----")
    data_len = struct.pack("<H", len(data_to_send))
    print(hexdump.hexdump(data_len))
    print(hexdump.hexdump(data_to_send))
    client.send(encode(data_len, init))
    client.send(encode(data_to_send, init))
