
#!/usr/bin/env python
import hexdump
import select
import socket

HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 1024   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

KEY = [0xf9, 0x8c, 0x63, 0x6d, 0x88, 0x71, 0x6d, 0xfe, 0x92, 0x8f, 0xff, 0x37,
       0xf3, 0xf3, 0xe2, 0x90, 0x46, 0xd5, 0x5e, 0x2c, 0xab, 0x61, 0xd4, 0x77,
       0x24, 0x94, 0xbc, 0x99, 0xa, 0x40, 0x4, 0x51, 0x34, 0xc5, 0x91, 0xa0,
       0x1, 0xa6, 0xce, 0xfb, 0xe6, 0x31, 0xef, 0xd4, 0x75, 0x25, 0xda, 0xaf,
       0x8f, 0xaf, 0x4, 0x5c, 0xc4, 0xe0, 0xed, 0xc5, 0x9e, 0x13, 0x4b, 0x62,
       0xd2, 0x4b, 0x3a, 0x90, 0x38, 0xfb, 0xf2, 0xc5, 0xbf, 0xb4, 0x5e, 0xb4,
       0x94, 0xa6, 0x93, 0x77, 0x8c, 0x69, 0x32, 0xa5, 0x2d, 0xa3, 0x98, 0x88,
       0x17, 0x4, 0x2f, 0x7a, 0xbe, 0xc1, 0x81, 0x9d, 0xaf, 0xaf, 0xb7, 0xf6,
       0xe4, 0xe5, 0x96, 0x87, 0x48, 0xb6, 0xee, 0xea, 0xc6, 0xf8, 0xe8, 0x78,
       0xd9, 0xc9, 0x90, 0xc3, 0xa2, 0x29, 0x0, 0xe0, 0xc5, 0x8a, 0xf, 0x5,
       0xe1, 0xf0, 0x5f, 0x78, 0x92, 0x73, 0xd8, 0x84, 0xf7, 0x80, 0x27, 0x62,
       0xe8, 0x93, 0xbc, 0x70, 0xd7, 0x3f, 0xc2, 0xf1, 0xb2, 0xd3, 0x94, 0x53,
       0x7a, 0x7d, 0x24, 0x79, 0x57, 0x16, 0x86, 0xc, 0x15, 0xc0, 0x4f, 0x29,
       0xd0, 0xbf, 0x7, 0x9c, 0x83, 0x5d, 0xa6, 0xc3, 0xd2, 0xdc, 0xde, 0xd7,
       0x5, 0x54, 0xd8, 0x81, 0xcd, 0x3e, 0xc0, 0xda, 0xb5, 0xb, 0xaa, 0xec,
       0x3d, 0xfe, 0xaa, 0xb6, 0xf4, 0x9c, 0x57, 0x44, 0xd4, 0xee, 0xfc, 0x5c,
       0x80, 0x13, 0x68, 0x59, 0xe9, 0xa3, 0x52, 0x8d, 0xde, 0x8c, 0xca, 0xd0,
       0x6e, 0xf2, 0x19, 0xec, 0x8, 0xcc, 0xee, 0xda, 0x59, 0x50, 0xc8, 0x81,
       0x4b, 0x9d, 0xa2, 0xb0, 0x78, 0x9d, 0x7d, 0x72, 0xec, 0xa2, 0xe3, 0x14,
       0xcb, 0xd0, 0x6b, 0x46, 0xe9, 0x18, 0x17, 0x5d, 0x7c, 0xee, 0x96, 0x3d,
       0x25, 0x7e, 0x70, 0x34, 0x8c, 0x87, 0xd, 0xd7, 0x2e, 0x80, 0xd8, 0xda,
       0xe1, 0x57, 0x79, 0x43, 0xc4, 0x6d, 0xfd, 0xf3, 0x78, 0xcc, 0x65, 0xbb,
       0xf2, 0xea, 0x89, 0x3c, 0x73, 0x99, 0x99, 0xff, 0xf7, 0x1c, 0xb6, 0xe2,
       0xfa, 0x91, 0x8f, 0x85, 0xc0, 0x6a]


# Get the token to send to the client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")

# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

# Set up lists for the newly found key values and plaintext
thekey = []
plaintext = []

# Truncate any existing file
with open('key', 'w') as f:
    f.truncate()

# Send data to the client
while True:
    rlist = select.select([client, server], [], [])[0]

    if client in rlist:
        buf = client.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Client -----")
            print(hexdump.hexdump(buf))
            decoded = []
            for b in buf:
                # We only want the first 282 bytes of plaintext:
                # 6 + 16 (uname) + 4 + 256 (pw)
                if CLI_IDX < 282:
                    with open('key', 'ab') as f:
                        f.write(bytes([KEY[CLI_IDX]]))
                    thekey.append(KEY[CLI_IDX])
                    plaintext.append(b ^ KEY[CLI_IDX] ^ init[CLI_IDX % len(init)])
                # For the remaining, we use the known plaintext to 
                # derive the unknown key
                else:
                    thebyte = b ^ plaintext[CLI_IDX % len(plaintext)] ^ init[CLI_IDX % len(init)]
                    with open('key', 'ab') as f:
                        f.write(bytes([thebyte]))
                    thekey.append(thebyte)
                CLI_IDX += 1
            server.send(buf)
            print(f"KEY LENGTH: {len(thekey)}")

    if server in rlist:
        buf = server.recv(BUFFER)
        if len(buf) > 0:
            print("\n----- Server -----")
            print(hexdump.hexdump(buf))
            client.send(buf)

