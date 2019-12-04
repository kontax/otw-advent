#!/usr/bin/env python
import hexdump
import select
import socket
from key import KEY

HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 1024   # Number of bytes to send/receive at a time

CLI_IDX = 0

# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(client)
print(client.fileno())
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")

# Wait for user to input
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")

# Create an initial key
init = bytes.fromhex('C0 84 2F D3 23 41 11 D4  B5 BD 4C 88 29 39 6F 4F')
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

# Send data to the client
while True:
    rlist = select.select([client], [], [])[0]

    if client in rlist:
        buf = client.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Client -----")
            decoded = []
            for b in buf:
                decoded.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
                CLI_IDX += 1
            print(hexdump.hexdump(bytes(decoded)))

