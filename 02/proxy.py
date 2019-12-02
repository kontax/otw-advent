#!/usr/bin/env python
import hexdump
import select
import socket

HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 1024   # Number of bytes to send/receive at a time

# Get the token to send to the client
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
buf = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(buf))
#buf = bytes.fromhex("E9 EC B7 F3 4E F4 24 1F  35 73 12 0F E3 62 1E 9B")
client.send(buf)

# Send data to the client
while True:
    rlist = select.select([client, server], [], [])[0]

    if client in rlist:
        buf = client.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Client -----")
            print(hexdump.hexdump(buf))
            server.send(buf)

    if server in rlist:
        buf = server.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Server -----")
            print(hexdump.hexdump(buf))
            client.send(buf)

