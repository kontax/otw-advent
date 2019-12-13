#!/usr/bin/env python
"""
----- Server -----
00000000: FD 32 89 62 3C 1D 82 3D B0 B4 DF 4D 3B 2C F9 D4
00000000: 14 BE F8 01 BE 69 85 A2 4F 5E 53 68 CD B5 7A 29 DE 94 

----- Server -----
00000000: BE 41 E1 D7 D5 4B A6 98 16 10 B5 42 20 0F B0 9D
00000000: 57 CD 90 B4 57 3F A1 07 E9 FA 39 67 D6 96 33 60 9D E7 

----- Server -----
00000000: 7C D0 47 92 96 E9 4E C4 CB CA 89 F0 7F 7B 1C 14
00000000: 95 5C 36 F1 14 9D 49 5B 34 20 05 D5 89 E2 9F E9 5F 76

----- Server -----
00000000: 17 82 99 70 6F D6 4D 51 24 71 07 42 BE 77 3E 18
00000000: FE 0E E8 13 ED A2 4A CE DB 9B 8B 67 48 EE BD E5 34 24

----- Server -----
00000000: 06 4C 89 53 8A F3 00 A5 66 EC F2 B2 53 65 0B 10
00000000: EF C0 F8 30 08 87 07 3A 99 06 7E 97 A5 FC 88 ED 25 EA
"""

v1 = [0x32, 0xBE]
v2 = [0x41, 0xCD]
v3 = [0xD0, 0x5C]
v4 = [0x82, 0x0E]
v5 = [0x4c, 0xc0]

for x in range(0xff):
    tmp1 = x ^ v1[0] ^ v1[1]
    tmp2 = x ^ v2[0] ^ v2[1]
    tmp3 = x ^ v3[0] ^ v3[1]
    tmp4 = x ^ v4[0] ^ v4[1]
    tmp5 = x ^ v5[0] ^ v5[1]

    if tmp1 == tmp2 == tmp3 == tmp4 == tmp5:
        print(hex(x))
