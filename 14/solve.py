#!/usr/bin/env python
from io import BytesIO

letters = [
    ['Q', '?', '0', '\\', 'H', '$', 'Y', ','],
    ['R', '-', 'L', '^', 'K', 'J', '_|', 'k'],
    ['s', '#', '_', '/', 'm', '=', 'f', '9'],
    ['7', 'd', '-', 'N', 'E', '4', 'q', 'r'],
    ['P', 'i', '|_', 'V', '`', '&', 'X', 'A'],
    ['n', '3', 'I', '|-', 'O', '*', ';', 'Z'],
    ['w', 'G', 'p', 'B', '8', 'c', 'S', 'j'],
    ['F', 'g', ':', 'e', 'b', 'y', '"' ,'v'],
    ['%', '+', '-|', '1', ' ', '!', 'M', '@'],
    ['h', '{', '2', 'x', 'W', '.', 'D', '}'],
    ['t', 'U', '|', 'C', 'T', 'z', '6', 'u'],
    ['|1', 'o', '>', 'a', '5', 'l', '<', "'"]
]

def extract_data(filename):
    png_end = b'IEND\xaeB`\x82'

    with open(filename, 'rb') as f:
        header = f.read(0x24)
        data = f.read()

    offset = data.find(png_end) + len(png_end)
    png = data[:offset]
    lines = data[offset:]

    return (header, png, lines)

def extract_letters(data):
    data = BytesIO(data)
    lines = []

    while data.read(7) == b'LiNe\0\0\0':
        length = int.from_bytes(data.read(1), 'little')

        output = []
        for i in range(int(length/2)):
            x = int.from_bytes(data.read(1), 'little')
            y = int.from_bytes(data.read(1), 'little')
            output.append(letters[y][x])

        lines.append(''.join(output))

    return lines


def solve():
    (h1, p1, l1) = extract_data('lines1.bin')
    (h2, p2, l2) = extract_data('lines2.bin')
    (h3, p3, l3) = extract_data('lines3.bin')
    (h4, p4, l4) = extract_data('lines4.bin')

    print(extract_letters(l1))
    print(extract_letters(l2))
    print(extract_letters(l3))
    print(extract_letters(l4))


if __name__ == '__main__':
    solve()
