#!/usr/bin/env python
from time import sleep

MAX_TIMESTAMP = 1000
keys = {
    0: [' ', '0'],
    1: ['.', ',', "'", '?', '!', '"', '1', '-', '(', ')', '@', '/', ':'],
    2: ['a', 'b', 'c', '2'],
    3: ['d', 'e', 'f', '3'],
    4: ['g', 'h', 'i', '4'],
    5: ['j', 'k', 'l', '5'],
    6: ['m', 'n', 'o', '6'],
    7: ['p', 'q', 'r', 's', '7'],
    8: ['t', 'u', 'v', '8'],
    9: ['w', 'x', 'y', 'z', '9'],
    10: ['@', '/', ':', '_', ';', '+', '&', '%', '*', '[', ']', '{', '}'],
    11: ['IME METHODS'],
    100: ['LT'],
    101: ['RT'],
    102: ['UP'],
    103: ['DN'],
    104: ['ACCEPT'],
    105: ['REJECT'],
}
ime = [
    'T9',
    'T9 Caps',
    'ABC',
    'ABC Caps'
]


def get_encoded_message(filename):
    # Read the text and convert each line to a set of integers
    text = open(filename, 'r').readlines()
    for i, t in enumerate(text):
        text[i] = [int(i) for i in t.strip().split(',')]

    # Use the first value as a timestamp, and rebase it to zero
    # as well as comparing it to the prev value rather than a base
    last_timestamp = 0
    for t in text:
        if last_timestamp == 0:
            last_timestamp = t[0]
            t[0] = 0
            continue

        timestamp = t[0]
        t[0] = timestamp - last_timestamp
        last_timestamp = timestamp

    return text

def decode_message(message):

    ime_method = ''         # IME method chosen
    ime_index = 0
    prev_timestamp = 0      # Timestamp for previous key
    prev_keycode = 0        # Code for previous key
    keycode_index = 0       # Index for cycling through keys
    cursor = 0
    decoded_message = []

    # Loop through each letter
    for c in message:

        timestamp = c[0]
        keycode = c[1]

        # Ignore accept/reject
        if keycode >= 104:
            decoded_message.insert(cursor, keys[keycode][0])
            cursor += 1
            prev_keycode = keycode
            prev_timestamp = 0
            keycode_index = 0

        # Choose the IME method
        elif keycode == 11:
            ime_method = ime[ime_index+1]
            ime_index += 1
            print(ime_method)

        # Left can be newline
        elif keycode == 100:
            decoded_message.insert(cursor, '')
            cursor += 1
            prev_keycode = keycode
            prev_timestamp = 0
            keycode_index = 0

        # Right is deleting a letter
        elif keycode == 101:
            cursor -= 1
            del decoded_message[cursor]
            #cursor += 1
            prev_keycode = keycode
            prev_timestamp = 0
            keycode_index = 0

        # Up is moving left without deleting
        elif keycode == 102:
            cursor -= 1

        # Down is moving right without deleting
        elif keycode == 103:
            cursor += 1


        # If a new regular key is pressed, store the result and note the code
        elif prev_keycode != keycode or \
             (prev_keycode == keycode and timestamp >= MAX_TIMESTAMP):
            decoded_message.insert(cursor, keys[keycode][0])
            cursor += 1
            prev_keycode = keycode
            prev_timestamp = 0
            keycode_index = 0

        # For regular keys, we need to keep track of how much time has already
        # passed, as well as the index we've already cycled through
        elif prev_timestamp < MAX_TIMESTAMP and prev_keycode == keycode:
            keycode_index += 1
            cursor -= 1
            decoded_message[cursor] = keys[keycode][keycode_index % len(keys[keycode])]
            cursor += 1
            prev_keycode = keycode
            prev_timestamp = 0

        else:
            print(f"ERROR: {timestamp}, {keycode}")

        # 
        printed_message = decoded_message.copy()
        printed_message[cursor-1] = '\033[4m' + decoded_message[cursor-1] + '\033[0m'
        print(f"{''.join(printed_message)}", end='\r')
        sleep(0.1)

    return decoded_message


msg1 = get_encoded_message('sms4.csv')
dec1 = decode_message(msg1)

