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
print(n(x))
