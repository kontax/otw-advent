#!/usr/bin/env python
import hexdump
import select
import signal
import socket
import sys
from time import sleep
import json
from io import BytesIO
from struct import pack, unpack
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
            return parse_use(stream_bytes)
        except Exception as ex:
            print_error(stream_bytes, ex)
            return {}

    else:
        return hexdump.hexdump(stream)

def initialize(stream):
    stream_length = num_convert(stream)
    if stream_length == 0:
        return {'msg': stream.read().decode()}

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

def parse_use(stream):
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
        storage['slots'] = f"{len(items)} / {num_convert(stream)}"
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
    stream_length = num_convert(stream)

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
        print(json.dumps(attack_details, indent=2))
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

def sz(b):
    return num_unconvert(len(b))

def sz_le(b):
    return pack('<H', len(b))

def login(username, password):
    x = b'\x0a' + sz(username) + username.encode() + \
        b'\x12' + sz(password) + password.encode()

    return b'\x12' + sz(x) + x

def attack(lvl):
    x = b'\x08' + num_unconvert(lvl)
    return b'\x1a' + sz(x) + x

def use(num=0):
    x = b'' if num == 0 \
            else b'\x18' + num_unconvert(num)
    return b'\x2a' + sz(x) + x

def item(direction, location, index):
    x = bytes([int(direction), int(location), 0x18, int(index)])
    return b'\x22' + sz(x) + x

def duplicate(location, index):
    x = bytes([0x08, int(location), 0x18, int(index), 0x10, int(location)])
    return b'\x22' + sz(x) + x

def buy_to_stash(index):
    x = b'\x08\x02\x18' + bytes([int(index)]) + b'\x10\x01'
    return b'\x22' + sz(x) + x

def sell_from_stash(index):
    x = b'\x08\x01\x18' + bytes([int(index)]) + b'\x10\x02'
    return b'\x22' + sz(x) + x

def send_command(sock, command_bytes, init):

    global KEY
    global CLI_IDX

    command_len = sz_le(command_bytes)

    print("\n----- Client -----")

    print(hexdump.hexdump(command_len))
    print(hexdump.hexdump(command_bytes))

    encoded = []
    for b in command_len + command_bytes:
        encoded.append(b ^ KEY[CLI_IDX % len(KEY)] ^ init[CLI_IDX % len(init)])
        CLI_IDX += 1

    sock.send(bytes(encoded))

def get_output(server, init):

    global BUFFER
    global KEY
    global SRV_IDX

    buf = server.recv(2)
    decoded_len = []
    for b in buf:
        decoded_len.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
        SRV_IDX += 1

    stream_length = unpack("<H", bytes(decoded_len))[0]
    SRV_IDX -= 2

    while len(buf) < (stream_length - 2):
        buf += server.recv(BUFFER)

    if len(buf) > 0:
        print("\n----- Server -----")

        decoded = []
        for b in buf:
            decoded.append(b ^ KEY[SRV_IDX % len(KEY)] ^ init[SRV_IDX % len(init)])
            SRV_IDX += 1

        parsed = parse(bytes(decoded))
        try:
            print(json.dumps(parsed, indent=2))
        except Exception as ex:
            print(ex)
            print(parsed)

        return parsed


def print_menu(stage="s"):
    if stage == "s":
        print("Options:")
        print("a - Attack")
        print("u - Use")
        print("i - Item")
        print("r - Raw hex")

    elif stage == "a":
        print("Options:")
        print("{n} - Level")

    elif stage == "u":
        print("Options:")
        print("{n} - Item Number")

    elif stage == "i":
        print("Options:")
        print_menu("id")
        print_menu("il")
        print_menu("ii")
    elif stage == "id":
        print(" - Direction:")
        print("   p - Put")
        print("   g - Get")
    elif stage == "il":
        print(" - Location:")
        print("   h - Shop")
        print("   t - Storage")
    elif stage == "ii":
        print(" - Index: {n}")


# Get the token to send to the client
with open('key', 'rb') as f:
    KEY = [int(x) for x in f.read()]

# Connect to the real server and get the initial response
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))

not_logged_in = True
while not_logged_in:
    username = input("Username: ")
    password = input("Password: ")

    send_command(server, login(username, password), init)
    output = get_output(server, init)
    not_logged_in = 'msg' in output

def signal_handler(sig, frame):
    server.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Fight 10 times to get 100 g
for i in range(10):
    print(f"Attack {i}")
    send_command(server, attack(3), init)
    send_command(server, use(), init)
    sleep(0.1)


# Buy an item from idx 1 for 5 rounds
for i in range(5):
    print(f"Buying {i}")
    send_command(server, buy_to_stash("1"), init)
    sleep(0.1)

    # Duplicate it 12 times
    for j in range(12):
        print(f"Duplicate {j}")
        send_command(server, duplicate("1", "0"), init)
        sleep(0.1)

    # Sell each one
    for j in range(13):
        print(f"Selling {j}")
        send_command(server, sell_from_stash("0"), init)
        sleep(0.1)

server.close()
CLI_IDX = 0
SRV_IDX = 0

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((HOST, SERVER_PORT))
init = server.recv(BUFFER)
print("\n----- Server -----")
print(hexdump.hexdump(init))
print("Sleeping for 20s to relogin")

sleep(20)
send_command(server, login(username, password), init)
output = get_output(server, init)

shop = [x for x in output['items'] if x['name'] == 'shop'][0]
index = [i for (i, v) in enumerate(shop['storage'][0]['items'])][0]

# Buy the scroll
send_command(server, item(0x08, 0x01, index), init)
get_output(server, init)

# Use the scroll
send_command(server, use("2"), init)
get_output(server, init)




print("Done")
exit(0)

# Send data to the client
while True:

    print_menu()
    cmd = input("Command: ")

    if cmd == "a":
        print_menu(cmd)
        try:
            lvl = int(input("Lvl: "))
        except:
            continue

        send_command(server, attack(lvl), init)
        get_output(server, init)

    elif cmd == "u":
        print_menu(cmd)
        try:
            num = int(input("Item number: "))
        except:
            continue

        send_command(server, use(num), init)
        get_output(server, init)

    elif cmd == "r":
        try:
            hex_bytes = bytes.fromhex(input("Enter hex bytes:\n"))
        except:
            continue

        send_command(server, hex_bytes, init)
        get_output(server, init)

    elif cmd == "i":
        print_menu(cmd)
        options = []
        d = ""
        l = ""
        i = 0
        while d not in ['p', 'g']:
            print_menu("id")
            d = input("Direction: ")
        while l not in ['h', 't']:
            print_menu("il")
            l = input("Location: ")
        try:
            print_menu("ii")
            i = int(input("Index: "))
        except:
            continue

        d = 0x10 if d == 'p' else 0x08
        l = 0x01 if l == 't' else 0x02

        send_command(server, item(d, l, i), init)
        get_output(server, init)

