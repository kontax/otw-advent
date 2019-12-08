#!/usr/bin/env python
import hexdump
import select
import socket
from key import KEY
from io import BytesIO


HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 4096   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

LOOKUP = {
    'lvl_up': 0x08,
    'xp'    : 0x10,
    'max_xp': 0x18,
    'lv'    : 0x20,
    'hp'    : 0x28,
    'max_hp': 0x30,
    'g'     : 0x38
}

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

def num_convert(stream):
    shift = 0
    ret = 0
    is_negative = True
    while is_negative:
        num = get_int(stream, 1)
        ret |= ((num & 0x7f) << shift)
        shift += 7
        is_negative = num >= 0x7f

    return twos_comp(ret, 64)

def get_int(stream_bytes, num):
    return int.from_bytes(stream_bytes.read(num), 'little')


def parse(stream):
    print(hexdump.hexdump(stream))
    stream_bytes = BytesIO(stream)
    stream_length = get_int(stream_bytes, 2)
    event = get_int(stream_bytes, 1)

    if event == 0x12:
        # Enemy 
        return parse_attack(stream_bytes)
    
    elif event == 0x1a:
        # Buy
        return buy_item(stream_bytes)

    else:
        return hexdump.hexdump(stream)

def buy_item(stream):
    stream_length = num_convert(stream)

    item_details = []
    item_details.append({'length': stream_length})
    item_details.append({'storage': get_items(stream)})
    item_details.append({'storage': get_items(stream)})
    item_details.append({'other': stream.read()})

    return {'items': item_details}

def get_items(stream):
    storage = []

    stage = get_int(stream, 1)
    length = num_convert(stream)
    offset = stream.tell()
    storage.append({'length': length})

    location = stream.read(2)
    if location == b'\x08\x02':
        storage.append({'name': 'shop'})
    else:
        storage.append({'name': 'bag'})
        stream.seek(stream.tell()-2)

    stage = get_int(stream, 1)
    items = []
    while stream.tell() - offset < length and stage == 0x12:
        items.append(get_item(stream))
        stage = get_int(stream, 1)

    storage.append({'items': items})
    stream.seek(stream.tell()-1)
    storage.append({'other': stream.read(length-(stream.tell()-offset))})
    return storage

def get_item(stream):
    item = []

    length = num_convert(stream)
    item.append({'length': length})

    next_attr = get_int(stream, 1)
    if next_attr == 0x08:
        item.append({'lvl': get_int(stream,1)})
        next_attr = get_int(stream, 1)

    if next_attr == 0x10:
        item.append({'dmg': num_convert(stream)})
        next_attr = get_int(stream, 1)

    if next_attr == 0x18:
        item.append({'hp': num_convert(stream)})
        next_attr = get_int(stream, 1)

    if next_attr != 0x22:
        raise AssertionError(f"{hex(next_attr)} != 0x22")
    #assert next_attr == 0x22
    buy_at = []
    length = get_int(stream, 1)
    buy_at.append({'length': length})
    buy_at.append({'SOMETHING': stream.read(2)})
    buy_at.append({'SOMETHING': stream.read(2)})

    assert get_int(stream, 1) == 0x18
    buy_at.append({'price': num_convert(stream)})

    item.append({'buy_at': buy_at})

    assert get_int(stream, 1) == 0x22
    sell_at = []
    length = get_int(stream, 1)
    sell_at.append({'length': length})
    sell_at.append({'SOMETHING': stream.read(2)})

    if length <= 2:
        return item

    assert get_int(stream, 1) == 0x18
    sell_at.append({'price': num_convert(stream)})

    item.append({'sell_at': sell_at})
    return item


def parse_attack(stream):
    stream_length = get_int(stream, 1)

    attack_details = []
    while get_int(stream, 1) == 0x0a:
        attack_length = get_int(stream, 1)
        assert get_int(stream, 1) == 0x08
        enemy_attack = num_convert(stream)

        assert get_int(stream, 1) == 0x10
        our_attack = num_convert(stream)

        # Store length plus initial byte plus last
        attack_details.append({'attack': {'attack': our_attack, 'defend': enemy_attack}})

    if get_int(stream, 1) == 0x2a or len(attack_details) == 0:
        # Low HP
        stream.seek(stream.tell()-2)
        attack_details.extend(get_summary_details(stream))
    else:
        # Won the attack
        stream.seek(stream.tell()-2)
        attack_details.extend(get_win_details(stream))

    return attack_details

def get_win_details(stream):

    # Attack specific increases
    attack_details = []
    assert stream.read(2) == b'\x10\x01'
    if get_int(stream, 1) == 0x18:
        attack_details.append({'xp_increase': get_int(stream, 1)})

    if get_int(stream, 1) == 0x20:
        attack_details.append({'gold_increase': get_int(stream, 1)})

    attack_details.extend(get_summary_details(stream))
    return attack_details


def get_summary_details(stream):
    # Totals
    attack_details = []
    assert get_int(stream, 1) == 0x2a
    summary_length = get_int(stream, 1)

    assert get_int(stream, 1) == 0x08
    attack_details.append({'lvl': get_int(stream, 1)})

    if get_int(stream, 1) == 0x10:
        attack_details.append({'xp': num_convert(stream)})

    assert get_int(stream, 1) == 0x18
    attack_details.append({'max_xp': num_convert(stream)})

    assert get_int(stream, 1) == 0x20
    attack_details.append({'another_lvl': num_convert(stream)})

    assert get_int(stream, 1) == 0x28
    attack_details.append({'hp': num_convert(stream)})

    assert get_int(stream, 1) == 0x30
    attack_details.append({'max_hp': num_convert(stream)})

    assert get_int(stream, 1) == 0x38
    attack_details.append({'gold': num_convert(stream)})

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

