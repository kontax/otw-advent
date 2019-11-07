#!/usr/bin/env python
from struct import *

xmm2    = 0
xmm0    = 0xAA55950D36FC2D0D24970AA5B980796D    # key?
#xmm0   = 0x10359A9759143030A3BF811F8BEB83D0
xmm3    = 0x41414141414141414141414141414141    # guess

# Potential values: 54 52 5E 30 6D 11 34 A0 90 38 51 36 80 1A FE F7
#                   AA 55 95 0D 36 FC 2D 0D 24 97 0A A5 B9 80 79 6D


def encrypt(xmm0, xmm3):

    xmm0 = xmm0 ^ xmm3
    bh   = 0x36
    bl   = 0xe5
    ax   = 0x7300
    shuf = 0x10
    
    while True:
        ax = ax >> 7
        al = int(ax / bl)
        ah = ax % bl
        ax = join_reg(ah, al)
        xmm1 = aeskeygenassist(xmm0, ah)    # xmm0: {0xb980796d, 0x24970aa5, 0x36fc2d0d, 0xaa55950d}
                                            # xmm1: {0x36886706, 0x06368866, 0xacfc2ad7, 0xd7acfc2b}

        xmm1 = pshufd(xmm1, 0xff)           # xmm1: {0x36886706, 0x06368866, 0xacfc2ad7, 0xd7acfc2b}
                                            # ->    {0xd7acfc2b, 0xd7acfc2b, 0xd7acfc2b, 0xd7acfc2b}
        
        while True:
            xmm2 = shufps(xmm0, xmm2, shuf) # xmm0: {0xb980796d, 0x24970aa5, 0x36fc2d0d, 0xaa55950d}
                                            # xmm2: {0x0,        0x0,        0x0         0x0       }
                                            # xmm2: {0x0,        0x0,        0x24970aa5, 0xb980796d}
            
            xmm0 = xmm0 ^ xmm2
            shuf = shuf ^ 0x9c
            if shuf > 127:
                break
        
        xmm0 = xmm0 ^ xmm1
        
        if split_reg(ax)[0] == bh:
            break
            
        aesenc(xmm3, xmm0)

    aesenclast(xmm3, xmm0)

"""
Splits a 32bit register into (high, low) bytes
"""
def split_reg(reg):
    return (reg >> 8, reg & 0xff)

"""
Joins the high and low 16 bits of a register into a single 32bit register
"""
def join_reg(high, low):
    return (high << 8) | low

"""
src:  [d, c, b, a]
n:    [3, 2, 1, 0]

output: [src[3], src[2], src[1], src[0]
"""
def pshufd(source, n):

    # Group source into 4 longs
    source_unpacked = unpack('<LLLL', source.to_bytes(16, 'little'))
    
    # Split out `n` into the 4 values that point to which source to copy over
    mask = [int('{:08b}'.format(n)[i:i+2], 2) for i in range(0, 8, 2)][::-1]
    
    # Return the source with the values in the place specified by the mask
    masked_value = [source_unpacked[n] for n in mask]
    
    return int.from_bytes(pack('<LLLL', 
                masked_value[0], masked_value[1], 
                masked_value[2], masked_value[3]), 'little')
                
"""
src:  [d, c, b, a]
dest: [z, y, x, w]
n:    [3, 2, 1, 0]

output: [dest[3], dest[2], src[1], src[0]
"""
def shufps(source, dest, n):

    # Group source and dest into 4 longs
    source_unpacked = unpack('<LLLL', source.to_bytes(16, 'little'))
    dest_unpacked   = unpack('<LLLL', dest.to_bytes(16, 'little'))
    
    # Split out `n` into the 4 values that point to which source to copy over
    mask = [int('{:08b}'.format(n)[i:i+2], 2) for i in range(0, 8, 2)][::-1]
    
    # Return the source with the values in the place specified by the mask
    masked_source = [source_unpacked[n] for n in mask[2:]]
    masked_dest   = [dest_unpacked[n] for n in mask[0:2]]
    
    return int.from_bytes(pack('<LLLL', 
                masked_dest[0], masked_dest[1], 
                masked_source[0], masked_source[1]), 'little')
    
    