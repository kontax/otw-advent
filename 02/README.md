# Day 2: Summer Adventure

## Overview

## Required Software

## Solving the challenge

### Step 1 - Intercepting data

There are two ports in play within the IP address given, 12021 is the server
and does nothing when we connect to it, and 12022 is the client which gives
us a code to type into the web-client when connecting. The problem is neither
of these gives us much data other than when we randomly type some letters, and
then very little.

What we need to do is connect both of these servers together while we sniff the
packets sent between them. Given that we can connect to both client and server,
we can set up a simple man-in-the-middle server using a simple python script:

```python
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
```

Now when we connect to the fake server within the web frontend, it's actually
talking to the real server but we can see the bytes sent from within our
script. 

### Step 2 - Decoding the output

The only initial values we can control are the username and password fields, 
which are limited to 16 and 256 characters respectively. The initial message 
from the server looks to be a random set of 256 bits, which is responded to by 
the client once a username and password combo is entered. This looks different 
for each new connection, confirming that some sort of obfuscation is in place.

By using slight modifications to the username and password, we can establish
that the initial few bytes sent on are XOR'd with the username and password
(alongside some unknown bytes), as well as some other bytes that aren't known.
The first 6 bytes are unknown, but the next 16 + 4 + 256 can be derived by
looking at various combinations of username and password, specifically looking
at different lengths.

In order to get the first few bytes, we can send an invalid username/password
combo which allows us to continuously receive the same response from the 
server, and send the same response back. This can then be automated by making
a slight adjustment to the proxy script above:


```python
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
```

The incorrect username/password trick is then used with the maximum lengths for
each, until a key of sufficient length is extracted. It's important to type in
the same username and password at each stage, as it uses this plaintext for key
decoding each round. Also the plaintext length is set to 282, which is the 
maximum length available to send each round. 

The key output doesn't seem to have any repeated sections - it looks like a 
random output of some form. I have not found any way to derive the full key
however it may not be necessary as we can just extract as many bytes as 
necessary in order to perform the in game analysis in the next steps.

### Step 3 - Game analysis

The actual game looks straightforward enough. You play a character who fights
monsters for experience and cash, and can trade cash for new weapons of various
strengths from a seller. The seller also has a "scroll of infinite wisdom" 
which we can assume contains the flag, but it's far too expensive to by without
serious time put into playing. We need to find a way to get more cash by 
analysing the now decrypted data between client and server.
