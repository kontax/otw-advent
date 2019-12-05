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
SRV_IDX = 0

# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")

# Wait for user to input
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")
#input("Press any key when complete...")


# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

thekey = []

# Send data to the client
while True:
    rlist = select.select([client, server], [], [])[0]

    if client in rlist:
        buf = client.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Client -----")
            decoded = []
            for b in buf:
                decoded.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
                CLI_IDX += 1
            print(hexdump.hexdump(bytes(decoded)))
            test = input("Edit bytes? ")
            if test == 'Y' or test == 'y':
                print("Original: ")
                print(' '.join(["{:02x}".format(x) for x in decoded]))
                new_buf = bytes.fromhex(input())
                CLI_IDX -= len(buf)
                new_buf_list = []
                for b in new_buf:
                    new_buf_list.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
                    CLI_IDX += 1
                print(hexdump.hexdump(buf))
                buf = bytes(new_buf_list)
                print(hexdump.hexdump(buf))
            server.send(buf)

    if server in rlist:
        buf = server.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Server -----")
            decoded = []
            for b in buf:
                decoded.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
                SRV_IDX += 1
            print(hexdump.hexdump(bytes(decoded)))
            test = input("Edit bytes? ")
            if test == 'Y' or test == 'y':
                print("Original: ")
                print(' '.join(["{:02x}".format(x) for x in decoded]))
                new_buf = bytes.fromhex(input())
                SRV_IDX -= len(buf)
                new_buf_list = []
                for b in new_buf:
                    new_buf_list.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
                    SRV_IDX += 1
                print(hexdump.hexdump(buf))
                buf = bytes(new_buf_list)
                print(hexdump.hexdump(buf))
            client.send(buf)

