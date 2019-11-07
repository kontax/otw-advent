from itertools import product
from subprocess import Popen, PIPE, STDOUT
from string import ascii_uppercase, ascii_lowercase

all_chars = ''.join([chr(x) for x in range(0x20, 0x7f)])

chars = ascii_lowercase

for length in range(15, 16): # only do lengths of 1 + 2
    to_attempt = product(chars, repeat=length)
    i = 0
    for attempt in to_attempt:
        p = Popen(['./encr'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        output = p.communicate(input=''.join(attempt).encode())
        if len(output[0]) > 2:
            print(''.join(attempt))
            print(output[0])
            exit()
        i += 1
        if i == 0x7f-0x20:
            i = 0
            print(''.join(attempt), end='\r')
