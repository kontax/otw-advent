# Day 2: Summer Adventure

## Overview

This mostly boiled down to being a reverse engineering challenge, whereby a 
client/server games bytes needed to be intercepted and understood, before
being modified in order to grab the flags which were split between client
and server.

First steps are to create a proxy to intercept the bytes being sent, and
secondly to decrypt them. Once this had been achieved, understanding what
all the bytes meant was required. A bug in the game was then found which
allowed for duplicating and selling items in order to get enough cash to
buy the Scroll of Secrets to get the second half of the flag, before 
understanding the different types of items available in order to spoof the 
client from revealing the first half.

Overall this was quite a tricky challenge to complete, mainly due to the amount
of time required to understand the bytes.

## Required Software

* Python

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

This was the most time consuming part of the process - it involved looking at 
each stream of bytes after every event and trying to compare them for changes.
The first two bytes denote the length of the next stream of bytes in little
endian form. Any other length within the data was encoded in 7 bits rather than
8, meaning the following code needed to be used to decode it:

```python
from io import BytesIO

def n(stream):
    shift = 0
    ret = 0
    is_negative = True
    while is_negative:
        num = int.from_bytes(stream.read(1), 'little')
        ret |= ((num & 0x7f) << shift)
        shift += 7
        is_negative = num >= 0x7f

    return twos_comp(ret, 64)

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

x = BytesIO(bytes.fromhex('b0 09 ef 08 97 09 d6 08'))
print(n(x))
print(n(x))
print(n(x))
print(n(x))
```

I'm unsure whether this is common practice or not, though it wouldn't surprise
me to find out that was the case.

The data sent from the client was reasonably short, so it could be boiled down
to the following (parts in square brackets were optional):

Attack a monster:
`1a {sz} 08 {lv}`
    * sz: Length of the remaining bytes
    * lv: The level of the monster to attack

Use an item:
`2a {sz} [18 {idx}]`
    * sz: Length of the remaining bytes
    * idx: Index of the item in the bag

Transfer an item:
`22 {sz} [{dir} {loc} {dir} {loc} 18 {idx}]`
    * sz: Length of the remaining bytes
    * dir: Either 0x08 or 0x10, representing to or from respectively
    * loc: Either 0x01, 0x02 or blank, representing the stash, shop or bag respectively

After much messing around, it turns out that if you transfer an item to the same
location it gets duplicated rather than transfered. This allows you to simply 
duplicate the items in the stash and sell them before doing the same with a 
more expensive item. This can be repeated until enough cash has been acquired 
to buy the Scroll of Secrets.

The majority of the process is done with the [server_flag.py](files/server_flag.py)
script, and once we log in with the same username and password, we can buy the
scroll and use it to get the following message:

> Congratulations! Here is the server-side flag: _is_f0R_Th3_13373sT} The 
> client-side flag is clearly written on a piece of paper that was lost by the 
> shopkeeper some time ago. If only you could find it...

Great, not done yet...

### Step 4 - Client side

Thankfully most of the game analysis had been complete at this stage, a pretty
comprehensive understanding of what the bytes mean is required. Essentially a
fake server needs to be created and data sent to the client when required. This
is done within the [fake_server.py](files/fake_server.py) which responds with
bytes written in text form. 

The initial login bytes can be copied from a normal server response. This is
split into sections describing the state of the game. After the initial 2 byte
length, the byte `0A` denotes the beginning of the summary data. This includes
data such as health, cash, XP etc. Once these are parsed, three sections 
beginning with `1A` denote the start of the details about the items. Similar to
the transfer, `08 01` is for the stash, `08 02` is the shop, and the bag is 
left blank.

Each item within the location begins with `12` and contains various details 
about the item, including it's damage, buy price, and sell price. An item of
interest is the one begining with `08`, as it seems to be unique for each
type of item eg. `04` = Titanium Sword, `05` = Diamond Sword, `06` = Potion
and `08` = Scroll of Secrets.

A notable ommission is item `07`, so we can craft this by copying over the
Scroll of Secrets bytes and changing this one value (alongside the respective
byte lengths), and sending that on a response to buying something. This gives
us a new item in the shop with the following description:

> Mystery Letter
> A letter which reads: 'Here is the client side flag: AOTW{B14ckbOx_N3tw0rK_r3v


`AOTW{B14ckbOx_N3tw0rK_r3v_is_f0R_Th3_13373sT}`
