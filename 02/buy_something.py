#!/usr/bin/env python
import hexdump
import select
import socket
from key import KEY

HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 4096   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

def encode_cli(data, init):
    global CLI_IDX
    encoded = []
    for b in data:
        encoded.append(b ^ KEY[CLI_IDX] ^ init[CLI_IDX % len(init)])
        CLI_IDX += 1
    return bytes(encoded)

def encode_srv(data, init):
    global SRV_IDX
    encoded = []
    for b in data:
        encoded.append(b ^ KEY[SRV_IDX] ^ init[SRV_IDX % len(init)])
        SRV_IDX += 1
    return bytes(encoded)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")

# Wait for user to input
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")
input("Press any key when complete...")


# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

thekey = []

login = bytes.fromhex("12 00 12 10 0A 06 6A 7A 6A 41  6B 6C 12 06 6A 6B 6C 6A 6B 6C")
server.send(encode_cli(login, init))

resp = server.recv(2)
print(hexdump.hexdump(encode_srv(resp, init)))
client.send(resp)

resp = server.recv(BUFFER)
print(hexdump.hexdump(encode_srv(resp, init)))
client.send(resp)

buy = bytes.fromhex("9c 04 1A 99 09 0A B9 08 08 02 12 19          10 0A    22 0F   08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1B 08 01 10 14 22 0F 08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04 08 02 18 50 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 19 10 0A 22 0F 08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 19 10 0A 22 0F 08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1B 08 01 10 14 22 0F 08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04 08 02 18 50 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 19 10 0A 22 0F 08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1B 08 01 10 14 22 0F 08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04 08 02 18 50 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 19 10 0A 22 0F 08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1B 08 01 10 14 22 0F 08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04 08 02 18 50 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 19 10 0A 22 0F 08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04 08 02 18 08 12 1B 08 01 10 14 22 0F 08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04 08 02 18 50 12 1C 08 02 10 28 22 0F 08 02 10 01 18 98 F8 FF FF FF FF FF FF FF 01 22 05 08 02 18 A0 06 12 1C 08 03 10 50 22 0F 08 02 10 01 18 F0 B1 FF FF FF FF FF FF FF 01 22 05 08 02 18 C0 3E 12 1E 08 04 10 A0 01 22 0F 08 02 10 01 18 E0 F2 F9 FF FF FF FF FF FF 01 22 06 08 02 18 80 F1 04 12 1E 08 05 10 C0 02 22 0F 08 02 10 01 18 C0 FB C2 FF FF FF FF FF FF 01 22 06 08 02 18 80 EA 30 12 17 08 08 22 0F 08 02 10 01 18 80 D3 9D FB FF FF FF FF FF 01 22 02 08 02 18 E8 07 12 59 12 1D 08 06 18 A0 8D 06 22 0F   08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04    08 02    18 0A 12 19          10 0A    22 0F   08 02 10 01 18 F6 FF FF FF FF FF FF FF FF 01 22 04    08 02    18 08 12 1B 08 01    10 14    22 0F   08 02 10 01 18 9C FF FF FF FF FF FF FF FF 01 22 04    08 02    18 50  18 06 18 11")

server.send(encode_cli(login, init))

resp = server.recv(BUFFER)
print(hexdump.hexdump(encode_srv(resp, init)))
client.send(resp)

resp = server.recv(BUFFER)
print(hexdump.hexdump(encode_srv(resp, init)))
client.send(resp)
