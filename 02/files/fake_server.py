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
data_file = 'data_file'

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


# Create an initial key
init = bytes.fromhex('C0 84 2F D3 23 41 11 D4  B5 BD 4C 88 29 39 6F 4F')
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

# Send data to the client
while True:
    send_data = input(f"Send bytes: ")
    if send_data == 'Y' or send_data == 'y':
        with open('data_file', 'r') as f:
            data_to_send = bytes.fromhex(f.read())

    #data_to_send = bytes.fromhex(send_data)

    print("\n----- Server -----")
    print(hexdump.hexdump(data_to_send))
    encoded = []
    for b in data_to_send:
        encoded.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
        SRV_IDX += 1

    client.send(bytes(encoded))

