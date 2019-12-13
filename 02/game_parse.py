#!/usr/bin/env python
import hexdump
import select
import signal
import socket
import sys
import json
from key import KEY
from io import BytesIO
from traceback import print_exception


HOST = '3.93.128.89'
CLIENT_PORT = 12022
SERVER_PORT = 12021

BUFFER = 4096   # Number of bytes to send/receive at a time

CLI_IDX = 0
SRV_IDX = 0

SUMMARY_LOOKUP = {
    0x08: 'lvl_up',
    0x10: 'xp',
    0x18: 'max_xp',
    0x20: 'lv',
    0x28: 'hp',
    0x30: 'max_hp',
    0x38: 'g'
}

LOCATION = {
    0x01: 'stash',
    0x02: 'shop'
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
        is_negative = num > 0x7f

    return twos_comp(ret, 64)

def num_unconvert(val):
    val = val % (1<<64)
    bitlen = len("{:0b}".format(val))
    output = []
    while bitlen >= 0:
        if bitlen >= 7:
            output.append((val & 0x7f) | 0x80)
        else:
            output.append(val & 0x7f)

        val >>= 7
        bitlen -= 7

    return bytes(output)


def get_int(stream_bytes, num):
    return int.from_bytes(stream_bytes.read(num), 'little')

def print_error(stream, ex):
        print("---- ERROR DETAILS ---")
        print_exception(type(ex), ex, sys.exc_info()[2])
        print(f"{ex} @ {stream.tell()}")
        stream.seek(stream.tell()-2)
        print(hexdump.hexdump(stream.read()))
        stream.seek(0)
        print(hexdump.hexdump(stream.read()))


def parse(stream):
    stream_bytes = BytesIO(stream)
    stream_length = get_int(stream_bytes, 2)
    event = get_int(stream_bytes, 1)

    if event == 0x12:
        # Enemy 
        try:
            return parse_attack(stream_bytes)
        except Exception as ex:
            print_error(stream_bytes, ex)
            return {}
    
    elif event == 0x1a:
        # Buy
        try:
            return {'items': shop_item(stream_bytes)}
        except Exception as ex:
            print_error(stream_bytes, ex)
            return {}

    elif event == 0x0a:
        # Initialization
        try:
            return initialize(stream_bytes)
        except Exception as ex:
            print_error(stream_bytes, ex)
            return {}

    elif event == 0x22:
        # Use
        try:
            return use(stream_bytes)
        except Exception as ex:
            print_error(stream_bytes, ex)
            return {}

    else:
        return hexdump.hexdump(stream)

def initialize(stream):
    stream_length = num_convert(stream)
    if stream_length == 0:
        return {}

    assert stream.read(2) == b'\x08\x01'
    summary_details = get_summary_details(stream)

    item_details = []
    while get_int(stream, 1) == 0x1a:
        item_details.append(get_item_details(stream))

    return {
        'length': stream_length,
        'summary': summary_details,
        'items': item_details
    }

def shop_item(stream):
    stream_length = num_convert(stream)
    shop_items = {}
    shop_items['length'] = stream_length

    item_details = []
    assert get_int(stream, 1) == 0x0a

    # Once for shop, once for bag in either order
    item_details.append(get_item_details(stream))
    assert get_int(stream, 1) == 0x12
    item_details.append(get_item_details(stream))

    shop_items['items'] = item_details

    # Store remaining cash
    if get_int(stream, 1) == 0x18:
        shop_items['cash_remaining'] = num_convert(stream)
    else:
        stream.seek(stream.tell()-1)

    return shop_items

def use(stream):
    stream_length = num_convert(stream)
    assert get_int(stream, 1) == 0x08
    hp_restored = num_convert(stream)
    return {
        'length': stream_length,
        'hp_restored': hp_restored
    }


def get_item_details(stream):
    stream_length = num_convert(stream)

    item_details = {}
    storage = []
    item_details['length'] = stream_length

    stage = get_int(stream, 1)
    if stage == 0x08:
        item_details['name'] = LOCATION[get_int(stream, 1)]
    else:
        item_details['name'] = 'bag'
        stream.seek(stream.tell()-1)

    storage.append(get_items(stream))

    item_details['storage'] = storage

    return item_details

def get_items(stream):
    storage = {}

    stage = get_int(stream, 1)
    #length = num_convert(stream)
    offset = stream.tell()
    #storage['length'] = length

    items = []
    #while stream.tell() - offset < length and stage == 0x12:
    while stage == 0x12:
        items.append(get_item(stream))
        stage = get_int(stream, 1)

    storage['items'] = items

    # Store total slots
    if stage == 0x18:
        storage['slots'] = num_convert(stream)
    else:
        stream.seek(stream.tell()-1)

    return storage

def get_item(stream):
    item = {}

    length = num_convert(stream)
    item['length'] = length

    next_attr = get_int(stream, 1)
    if next_attr == 0x08:
        item['lvl'] = num_convert(stream)
        next_attr = get_int(stream, 1)

    if next_attr == 0x10:
        item['dmg'] = num_convert(stream)
        next_attr = get_int(stream, 1)

    if next_attr == 0x18:
        item['hp'] = num_convert(stream)
        next_attr = get_int(stream, 1)

    assert next_attr == 0x22
    buy_at = {}
    length = get_int(stream, 1)
    buy_at['length'] = length
    buy_at['shop?'] = stream.read(2).hex()
    buy_at['bag?'] = stream.read(2).hex()

    assert get_int(stream, 1) == 0x18
    buy_at['price'] = num_convert(stream)

    item['buy_at'] = buy_at

    assert get_int(stream, 1) == 0x22
    sell_at = {}
    length = get_int(stream, 1)
    sell_at['length'] = length
    sell_at['shop?'] = stream.read(2).hex()

    if length <= 2:
        item['sell_at'] = sell_at
        return item

    assert get_int(stream, 1) == 0x18
    sell_at['price'] = num_convert(stream)

    item['sell_at'] = sell_at
    return item


def parse_attack(stream):
    stream_length = get_int(stream, 1)

    attack_details = {}
    attack_details['rounds'] = []
    next_value = get_int(stream, 1)
    while next_value == 0x0a:
        attack_length = get_int(stream, 1)
        assert get_int(stream, 1) == 0x08
        enemy_attack = num_convert(stream)

        assert get_int(stream, 1) == 0x10
        our_attack = num_convert(stream)

        # Store length plus initial byte plus last
        attack_details['rounds'].append({'attack': our_attack, 'defend': enemy_attack})
        next_value = get_int(stream, 1)

    if next_value == 0x2a:
        # Low HP
        stream.seek(stream.tell()-1)
        attack_details.update(get_summary_details(stream))
    else:
        # Won the attack
        stream.seek(stream.tell()-1)
        attack_details.update(get_win_details(stream))

    return attack_details

def get_win_details(stream):

    # Attack specific increases
    attack_details = {}
    assert stream.read(1) == b'\x10'
    attack_details['lvl'] = num_convert(stream)
    if get_int(stream, 1) == 0x18:
        attack_details['xp_increase'] = num_convert(stream)

    if get_int(stream, 1) == 0x20:
        attack_details['gold_increase'] = num_convert(stream)

    attack_details.update(get_summary_details(stream))
    return attack_details


def get_summary_details(stream):
    summary_details = {}
    stage = get_int(stream, 1)
    assert stage == 0x2a or stage == 0x12
    length = num_convert(stream)
    offset = stream.tell()

    summary_details['length'] = length
    while stream.tell() - offset < length:
        lookup = get_int(stream, 1)
        summary_details[SUMMARY_LOOKUP[lookup]] = num_convert(stream)

    return summary_details


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

def signal_handler(sig, frame):
    server.close()
    client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Send data to the client
while True:
    rlist = select.select([client, server], [], [])[0]

    """
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
    """


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
            output.extend(decoded)
            if len(output) > 2:
                parsed = parse(bytes(output))
                try:
                    print(json.dumps(parsed, indent=2))
                except Exception as ex:
                    print(ex)
                    print(parsed)
                output = []

            else:
                print(hexdump.hexdump(buf))

            client.send(buf)

