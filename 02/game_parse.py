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

def num_convert(num1, num2):
    # Convert the bytes into a number
    # Byte1 is the initial, byte2 gets added to the first nibble
    # of byte1, turned into decimal, and appended, before being
    # turned back into hex.
    #
    # eg. 0xAC 0x02
    #     0xA + 0x02 = 0xC = 12
    #     return 0x12C

    high, low = num1 >> 4, num1 & 0x0F
    return int(str(high + num2) + hex(low).replace('0x', ''), 16)


def parse(stream):
    stream_length = int.from_bytes(stream[:2], 'little')
    stream = stream[2:]

    if stream[0] == 0x12:
        # Enemy 
        return parse_attack(stream)

    else:
        return hexdump.hexdump(stream)

def parse_attack(stream):
    stream_length = stream[1]
    stream = stream[2:]

    attack_details = []
    while stream[0] == 0x0a:
        attack_length = stream[1]
        assert stream[2] == 0x08
        if stream[4] == 0x10:
            enemy_attack = stream[3]
            next_opt = 4
        else:
            enemy_attack = num_convert(stream[3], stream[4])
            next_opt = 5

        assert stream[next_opt] == 0x10
        if next_opt + 2 == attack_length:
            our_attack = stream[next_opt+1]
        else:
            our_attack = num_convert(stream[next_opt+1], stream[next_opt+2])
        # Store length plus initial byte plus last
        attack_details.append({'attack': {'attack': our_attack, 'defend': enemy_attack}})
        stream = stream[attack_length+2:]

    if stream[0] == 0x2a or len(attack_details) == 0:
        # Low HP
        attack_details.extend(get_summary_details(stream))
    else:
        # Won the attack
        attack_details.extend(get_win_details(stream))

    return attack_details

def get_win_details(stream):

    # Attack specific increases
    attack_details = []
    assert stream[:2] == b'\x10\x01'
    stream = stream[2:]
    if stream[0] == 0x18:
        attack_details.append({'xp_increase': stream[1]})
        stream = stream[2:]

    if stream[0] == 0x20:
        attack_details.append({'gold_increase': stream[1]})
        stream = stream[2:]

    attack_details.extend(get_summary_details(stream))
    return attack_details


def get_summary_details(stream):
    # Totals
    attack_details = []
    assert stream[0] == 0x2a
    summary_length = stream[1]
    stream = stream[2:]
    assert len(stream) == summary_length

    assert stream[0] == 0x08
    attack_details.append({'lvl': stream[1]})
    stream = stream[2:]

    if stream[0] == 0x10:
        if stream[2] == 0x18:
            attack_details.append({'xp': stream[1]})
            stream = stream[2:]
        else:
            attack_details.append({'xp': num_convert(stream[1], stream[2])})
            stream = stream[3:]

    assert stream[0] == 0x18
    if stream[2] == 0x20:
        attack_details.append({'max_xp': stream[1]})
        stream = stream[2:]
    else:
        attack_details.append({'max_xp': num_convert(stream[1], stream[2])})
        stream = stream[3:]

    assert stream[0] == 0x20
    attack_details.append({'another_lvl': stream[1]})
    stream = stream[2:]

    assert stream[0] == 0x28
    if stream[2] == 0x30:
        attack_details.append({'hp': stream[1]})
        stream = stream[2:]
    else:
        attack_details.append({'hp': num_convert(stream[1], stream[2])})
        stream = stream[3:]

    assert stream[0] == 0x30
    if stream[2] == 0x38:
        attack_details.append({'max_hp': stream[1]})
        stream = stream[2:]
    else:
        attack_details.append({'max_hp': num_convert(stream[1], stream[2])})
        stream = stream[3:]

    assert stream[0] == 0x38
    if len(stream[1:]) > 1:
        attack_details.append({'gold': num_convert(stream[1], stream[2])})
    else:
        attack_details.append({'gold': stream[1]})

    return attack_details


# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, CLIENT_PORT))
server_id = client.recv(1024).split()[2]
print(f"Server ID: {server_id.decode()}")

# Wait for user to input
print(f"Visit http://3.93.128.89:12020/ and enter {server_id.decode()}")


# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))
client.send(init)

thekey = []
output = []

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
            output.extend(decoded)
            if len(output) > 2:
                print(parse(bytes(output)))
                output = []

            client.send(buf)

