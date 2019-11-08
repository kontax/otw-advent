# Day 0: Challenge Zero

## Overview

This challenge was a mixture of categories, but mainly boiled down to having to understand and decrypt an AES self-modifying MBR binary. It started with a web-page, for which different browsers gave different hints to where to go. Once netcat was used, a uu-encoded base64 string was extracted and turned into a binary file which required qemu to run and debug. This binary had an AES encrypted section towards the end, which used a key contained in the last 16 bytes of the binary. A decryption routine had to be written by extracting each of the round-keys used in encryption in order to decrypt the key.

## Required Software

* curl: Allows us to get the initial base64 string
* sharutils: Contains uudecode
* qemu-system: Used to run the binary
* GDB: For debugging the binary
* IDA: Used for reverse-engineering the binary
* nasm: Assembler used to assemble the final solver

## Step 1 - Gathering the hints

The first step was to visit the [URL given](https://advent2019.overthewire.org/challenge-zero). This gave an image of a fireplace, as well as a hint. Looking at the source code revealed a comment: `<!-- browser detected: chrome -->`, and the first sentence in the page was `Fox! Fox! Burning bright! In the forests of the night!`. Clearly this hints towards using Firefox for viewing the page. If you keep following the browser suggestions using a user-agent switcher, the following list of hints are supplied:

*Edge*
This is quite the browser safari, don't you agree?
Hint: Pause qemu by add -S to the args and type 'c' in the monitor

*Opera*
Music for the masses
Hint: Try reading between the lines.

*Safari*
Put your hands up, this is the Chrome Shop mafia!
Hint: qemu-system-x86_64 boot.bin -cpu max -s

*Chrome*
Fox! Fox! Burning bright! In the forests of the night!
Hint: $ break *0x7c00

*Firefox*
Did you know: Plain text goes best with a text browser.
Hint: $ target remote localhost:1234

*Lynx*
D0NT PU5H M3 C0Z 1M C1053 T0 T3H 3DG3
Hint: If only the flames wouldn't move that much...

*wget*
Is that a curling iron in your pocket or are you just happy to see me?

*curl*
[ascii flames]

## Step 2 - Extracting the binary

The curl output is interesting in that it's a constantly changing ascii representation of the GIF on the website, a sample of which is given below. Directly saving this to a file is tricky, as all the bash formatting codes are output too. Cleaning this up leaves 5 distinct "images".

```
##########################################################################
###############################Ym#########################################
###############################V##########################################
###############################naW########################################
###############################4gN########################################
###############################jQ0########################################
#############################IGJ#vb3######################################
#############################QuY#mlu######################################
#############################Ck1#eQy######################################
#############################dgQ#01C###########Ll#########################
#############################A#oWz#BPY#########CF#########################
#############################cMGB#eQi#N########SI#############2###########
#############################BA#XiN#bQF#########x############AI###########
##############i############NS#K2A#jUi#N########AI#z##########Bg###########
##############J############iN###SK0#BPT#z######lcWit#########YYD##########
#############lA############X#lo##K#TVg#xR######V#MzO#########1g4##########
#############Pz5#######CU##W#ArX#GA/#Qyd#gU##z#E4X#CM########3MDo#########
############vYE#F######VI###1gn#X2A#####nWV###5bS#1##########km#Pz5#######
############CNm#A####kX#0############tZ#Okp###UI0#x##########UM#A#########
###########pNWl1#####aIV#############9RI#####V49#PF########w#vK###########
###########m#A7U###D8w#XEg###########nQC#Fe##W#iMw########################
###########YDl#AX##0#8nT#iF##########dOUB###cWC#VdT#######################
############V######Qi#Tk5#TT0#########I1X#Vom#MGB#a#######################
###################X1#peC#k00#J####1Q#vKm#A4Y#D9AXE#######################
###################g#nLk#AvY#GBc###SSc#oLy#YkK#Cde########################
#################WCd#VVV#o+##R#k1########g#####Jj##g######################
#################vW##1###0pR###############iNeXzh###OXj###################
########################RWT###########################S###################
###############cv###IVp#############################g##P1#Y###############
##########################################################################
#############################KT#V##xY#QEZ#####P###########################
#########################R1#F##GI#1NL###P1I#kNU###Y#######################
###################jV###y####Mp######X1##B#fJ##l#####Qh###################
##########################################################################
```

As the letters within the hashes change with each iteration, removing the hashes from the output and concatenating the result leaves us with what looks like a base64 encoded string. The equals signs are a dead giveaway here.

```
YmVnaW4gNjQ0IGJvb3QuYmluCk1eQydgQ01CLlAoWzBPYCFcMGBeQiNSI2BAXiNbQFxAIiNSK2AjUiNAIzBgJiNSK0BPTzlcWitYYDlAXloKTVgxRVMzO1g4Pz5CUWArXGA/QydgUzE4XCM3MDovYEFVI1gnX2AnWV5bS1kmPz5CNmAkX0tZOkpUI0xUMApNWl1aIV9RIV49PFwvKmA7UD8wXEgnQCFeWiMwYDlAX08nTiFdOUBcWCVdTVQiTk5TT0I1XVomMGBaX1peCk00J1QvKmA4YD9AXEgnLkAvYGBcSScoLyYkKCdeWCdVVVo+Rk1gJjgvW10pRiNeXzhOXjRWTScvIVpgP1YKTVxYQEZPR1FGI1NLP1IkNUYjVyMpX1BfJlQhIUYjXl8iQCM7Jz8pUVhcNjgvW1wkWF8nMCc5QFxYVy1DSwpNU0Y4Ly4tVzhQWzAuSyMxIj1gOFFWXFQwWl8vIzNUQDUpVihXLEI0UChSOEcpRihELCJUTzhBYCE9RihWCk0qQkxROENMRyhTIUMwRF0oJEIsUSwzNE0sIjlYOEQpLzJgJE0rUj1CKCIsQSo2KFUqUzhKOEItQitSVEYKTSlTYEw4QCQyJVYpWCREKSo4REkiRCkiMEQpIjBUKC9LQlFeIU9aLFAsITE5RVlIVSQhUSIwXjBeKz84PQpNTEdZWicsS18iND4nK05fVUsmPUEtRjsqJUNcJVw9PSgvM0tUYFosMlo5SCMiIichITheUiRANztdQi1YCk0sIUlCIV4wR15cIktWSkE7QjNMWltVV0gqWiZOW1wxQz5CST4hKjpdPEsvSCUrMywiO1tCQD47RTcySVYKTT4kWiU/KlE0YEZfUSdCIktEV1guMkJeWUBaOEYtMiQ4LzBNRFYnLl1dX1g6QCM5MS4pIkAtISVNLCVZMgoxNSZVWUArRkUiSTxEIzJXXC1AVjU1OkhgCmAKZW5kCg==
```

Decoding this leaves us with a uu-encoded file named boot.bin:
```

begin 644 boot.bin
M^C'`CMB.P([0O`!\0`^B#R#`@^#[@\@"#R+`#R#@#0`&#R+@OO9\Z+X`9@^Z
MX1ES3;X8?>BQ`+\`?C'`S18\#70:/`AU#X'_`'Y^[KY&?>B6`$_KY:JT#LT0
MZ]Z!_Q!^=<\/*`;P?0\H'@!^Z#0`9@_O'N!]9@\X%]MT"NNSOB5]Z&0`Z_Z^
M4'T/*`8`?@\H'.@/``\I'(/&$('^X'UUZ>FM`&8/[])F#^_8N^4VM'/!Z`?V
M\X@FOGQF#SK?R$5F#W#)_P_&T!!F#^_"@#;'?)QX\68/[\$X_'0'9@\XW-CK
MSF8/.-W8P[0.K#1"=`8QV\T0Z_/#3T@5)V(W,B4P(R8G)F(D,"TO8A`!=F(V
M*BLQ8CLG(S!C0D]($B,Q,34M,"9X8D)/2`$M+R=B(",A*6(U*S8J8B-B+RTF
M)S`L8@$2%V)X$D)*8DI"D)"0D)"0T(/KBQ^!OZ,P,!19EYHU$!Q"0^0^+?8=
MLGYZ',K_"4>'+N_UK&=A-F;*%C\%\==(/3KT`Z,2Z9H#""'!!8^R$@7;]B-X
M,!IB!^0G^\"KVJA;B3LZ[UWH*Z&N[\1C>BI>!*:]<K/H%+3,";[B@>;E72IV
M>$Z%?*Q4`F_Q'B"KDWX.2B^Y@Z8F-2$8/0MDV'.]]_X:@#91.)"@-!%M,%Y2
15&UY@+FE"I<D#2W\-@V55:H`
`
end
```

We can further decode this with `uudecode boot.uu`, leaving us with a boot.bin binary file. The full command is given below, with boot.b64 containing the base64 string.
```
$ base64 -d boot.b64 | uudecode
```

## Step 3 - Analysing the binary

First things first, we need to know what type of file we're dealing with.

```bash
$ file boot.bin
boot.bin: DOS/MBR boot sector

$ strings boot.bin
'b72%0#&'&b$0-/b
vb6*+1b;'#0cBOH
#115-0&xbBOH
-/'b #!)b5+6*b#b/-&'0,b
BJbJB
ga6f
cz*^
]*vxN
m0^RTmy
```

So it's a Master Boot Record sector of 512 bytes. The hints given to us from the web pages indicate that we should run it using qemu, but first I opened up the file in IDA to see if anything popped out. I used the "Intel 8086" processor type due to the code being 16 bit, although I'm not entirely sure this is necessary. The entry point looks to be the first byte of the binary, which translates to valid x86 code. Two functions are extracted, one which contains various AES assembly instructions, and the other which writes to the screen according to IDA comments. Not too far from the initial entry point is another `int` instruction, which takes keyboard input.

## Step 4 - Getting up and running

I had a few issues with this, due to both the GDB plugin GEF not being able to correctly interpret the instructions, and also having GDB incorrectly calculate the values of the xmm* registers during execution. I'll discuss how I overcame these shortly, but firstly the hints given in the web page show us how to run the binary.

The emulator `qemu` can be used to run various binaries, this one included. As this is an MBR file, we use the qemu-system-i386 version with various flags. 
* `-s` is used to create a GDB server on port 1234 to run in
* `-S` pauses the binary before execution, allowing GDB to start running from the entry point
* `-cpu` sets the processor to use (I'm not sure what `max` refers to)
* `-nographic` runs the binary within the terminal rather than the qemu frontend

Once the binary is running, it waits for a GDB instance to attach to it before it continues. This was also run with various flags:
* `-ex 'target remote 127.0.0.1:1234'` attaches to the local gdb-server, the qemu instance in this case
* `-ex 'set architecture i8086'` sets the processor to 16-bit mode (this didn't seem to have much effect in my case)
* `-ex 'b *0x7c00'` sets a breakpoint at the entrypoint of the binary

Given the issues I alluded to earlier, I actually ran qemu on my Arch Linux VM, but GDB on my WSL windows host with the pwndbg plugin. This fixed most of the issues with instructions, however the issues with the xmm registers persisted.

```
$ qemu-system-i386 boot.bin -cpu max -s -S -nographic
SeaBIOS (version ?-20191013_105130-anatol)


iPXE (http://ipxe.org) 00:03.0 C980 PCI2.10 PnP PMM+07F93480+07EF3480 C980
                                                                               


Booting from Hard Disk...

We upgraded from RC4 this year!
Password: 
```

```
$ gdb -q -ex 'target remote 192.168.204.3:1234' -ex 'set architecture i8086' -ex 'b *0x7c00' -ex 'b *0x7c62' -ex 'c'
pwndbg: loaded 180 commands. Type pwndbg [filter] for a list.
pwndbg: created $rebase, $ida gdb functions (can be used with print/break)
Remote debugging using 192.168.204.3:1234
warning: No executable has been specified and target does not support
determining executable automatically.  Try using the "file" command.
0x0000fff0 in ?? ()
The target architecture is assumed to be i8086
Breakpoint 1 at 0x7c00
Breakpoint 2 at 0x7c62
Continuing.

Breakpoint 1, 0x00007c00 in ?? ()
Could not check ASLR: Couldn't get personality
LEGEND: STACK | HEAP | CODE | DATA | RWX | RODATA
──────────────────────────────────────[ REGISTERS ]──────────────────────────────────────
 EAX  0xaa55 —▸ 0 —▸ 0xf000ff53 ◂— 0
 EBX  0 —▸ 0xf000ff53 ◂— 0
 ECX  0 —▸ 0xf000ff53 ◂— 0
 EDX  128 —▸ 0xf000ff53 —▸ 0 ◂— push   ebx /* 0xf000ff53 */
 EDI  0 —▸ 0xf000ff53 ◂— 0
 ESI  0 —▸ 0xf000ff53 ◂— 0
 EBP  0 —▸ 0xf000ff53 ◂— 0
 ESP  0x6f00 —▸ 0xf000d002 —▸ 0 —▸ 0xf000ff53 ◂— 0
 EIP  0x7c00 —▸ 0x8ec031fa —▸ 0 —▸ 0xf000ff53 ◂— 0
───────────────────────────────────────[ DISASM ]────────────────────────────────────────
 ► 0x7c00    cli
   0x7c01    xor    eax, eax
   0x7c03    mov    ds, eax
   0x7c05    mov    es, eax
   0x7c07    mov    ss, eax
    ↓
   0x7c07    mov    ss, eax
────────────────────────────────────────[ STACK ]────────────────────────────────────────
00:0000│ esp  0x6f00 —▸ 0xf000d002 —▸ 0 —▸ 0xf000ff53 ◂— 0
01:0004│      0x6f04 —▸ 0 —▸ 0xf000ff53 ◂— 0
02:0008│      0x6f08 —▸ 0x6f5e —▸ 0 —▸ 0xf000ff53 ◂— 0
03:000c│      0x6f0c —▸ 0x82ff —▸ 0 —▸ 0xf000ff53 ◂— 0
04:0010│      0x6f10 —▸ 0x8340 —▸ 0 —▸ 0xf000ff53 ◂— 0
05:0014│      0x6f14 —▸ 0 —▸ 0xf000ff53 ◂— 0
... ↓
07:001c│      0x6f1c —▸ 0x82ff —▸ 0 —▸ 0xf000ff53 ◂— 0
──────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────
 ► f 0     7c00
─────────────────────────────────────────────────────────────────────────────────────────
Breakpoint *0x7c00
pwndbg> c
Continuing.

```

## Step 5 - Debugging

Using a mixture of IDA and GDB, it became clear that the program does the following:

1. Uses the CPUID instruction to get and set specific CPU flags, most likely to set up [SSE](https://en.wikipedia.org/wiki/Streaming_SIMD_Extensions)
2. Prints the output to the screen using the function at offset 0x7ce8
   This takes data from offset 0x7cf6 and XOR's it with 0x42 in order to print out the text on the screen up to the 'Password:' prompt
3. Read characters until the newline character (0xd) at offset 0x7c3a, storing the data into memory at offset 0x7e00.
4. If the password entered was 16 characters it moves on to the encryption routine, otherwise it presents the password prompt again.
5. Run the first encryption routine at offset 0x7c62. This takes the password entered at 0x7e00, and a key from 0x7df0. On completion it checks the bytes at offset 0x7de0 to see if the encrypted output matches, and if so jumps to the second stage encryption.
6. Run the second encryption routine, which uses the password as a key to encrypt the bytes from 0x7d50 to 0x7de0 (not inclusive) 16 bytes at a time.
7. Once the bytes have been "encrypted", code execution jumps into those bytes.

## Step 6 - Reverse-engineering the AES routine

When debugging the encryption routine, I had an issue that the xmm registers seemed to be shifted over by 8 bytes. This caused an issue whereby, for example, only the first 12 bytes of the key were visible in the register, with 8 bytes of the password entered in the last 8 bytes, as opposed to the full 16 bytes expected. This ultimately did not have any effect on the outcome so must just have been an issue with either GDB or qemu, however it caused a bit of confusion when debugging. In the end I just extracted the assembly and re-assembled it locally which seemed to cause the correct values to be shown. This local file allowed for much easier reversing too, so was worth it in the end.

The first option I researched was trying to extract the second key, however this proved fruitless as no plaintext was known beforehand. In the end I used two resources to figure out how the AES encryption routine works, and then implemented a decryption routine in assembly in order to extract the key. This was possible as the initial key was given to us (the last 16 bytes of the binary). The two resources were:
* [Rijndael Animation](http://formaestudio.com/rijndaelinspector/archivos/rijndaelanimation.html)
* [Intel AES Manual](https://software.intel.com/sites/default/files/article/165683/aes-wp-2012-09-22-v01.pdf)

To summarize, AES used here works as follows:
1. Take the plaintext (our password) and key (the bytes at 0x7df0: `0xaa55950d36fc2d0d24970aa5b980796d`).
2. XOR the plaintext with the key as a "whitening" step.
3. Run the following algorithm 10 times:
   1. Run the AESKEYGENASSIST instruction on the key.
   2. Perform some functions on the output key, named the "key expansion" steps, which creates the final "Round Key"
   3. Encrypt the current step of the plaintext using the AESENC instruction.
4. For the final step, use the AESENCLAST instruction for the final round of encryption

The key point to note here is that a new key is generated - the "Round Key" - for each iteration of the algorithm. This key is then XOR'd with the plaintext each round to generate the final ciphertext. Accordingly, the decryption routine takes each round key and runs the algorithm in reverse, which is what is necessary for us to implement. With that said, we need to grab the key just before the AESENC and AESENCLAST instructions are called, and save them for use in our decryption routine.

```
(gdb) b *0x7cdb
Breakpoint 3 at 0x7cdb
(gdb) b *0x7ce2
Breakpoint 4 at 0x7ce2
(gdb) display/x $xmm0->v2_int64
1: /x $xmm0->v2_int64 = {0x0, 0x0}
(gdb) c
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x7c47a2ee4abb8fe3, 0xd7acfc2bd61237e3}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x492661d33561c33d, 0x11f6c9989f345630}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x746f6854e609756, 0x4db18b59872a0b5}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0xe7617550e02783d5, 0xd54640e87f13d5e5}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x70d39f1597b2ea45, 0xd9d27d130fc04af0}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x1c82a6366c513923, 0x8c76baf61342ecc6}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0x3f4d60fd23cfc6cb, 0xb47d2c8e2c0f8c3b}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0xb16d2f3a8e204fc7, 0xe27176e49d62a301}
(gdb)
Continuing.

Breakpoint 3, 0x00007cdb in ?? ()
1: /x $xmm0->v2_int64 = {0xeefc43e05f916cda, 0x7c5eaa11739ee0e1}
(gdb)
Continuing.

Breakpoint 4, 0x00007ce2 in ?? ()
1: /x $xmm0->v2_int64 = {0x985307f076af4410, 0xf88f0bd7ebcde711}
(gdb)
```

Now given the keys, and the ciphertext we're testing against located at 0x7de0 (0x54525E306D1134A090385136801AFEF7), we can create a function which decrypts that ciphertext.

```assembly
global _start, main

section .bss
    output: resq 0x11                   ; Variable to hold the plaintext - used to print at the end

section .text

_start:
    call    main

main:
    mov     ecx, rndkey                 ; Load the address of the keys
    movaps  xmm3, [ctxt]                ; Load the ciphertext into xmm3
    movaps  xmm0, [ecx]                 ; Load the first key into xmm0
    pxor    xmm3, xmm0                  ; Perform the initial XOR
    call    decrypt

    movaps  [output], xmm3              ; Move the decrypted ciphertext into the output variable
    mov     [output+0x10], byte 0xa     ; Add a newline to the end of the string
    call    print                       ; Print the result to screen
    call    exit                        ; Exit

decrypt:
    add     ecx, 0x10                   ; Move to the next key
    movaps  xmm0, [ecx]                 ; Load the next key into xmm0
    aesimc  xmm0, xmm0                  ; Perform the reverse key expansion step
    aesdec  xmm3, xmm0                  ; Perform the decryption
    cmp     ecx, rndkey+0x90            ; Check if we've reached the 2nd to last key
    jnz     decrypt

    add     ecx, 0x10                   ; Move to the final key
    movaps  xmm0, [ecx]                 ; Insert the final key into xmm0
    aesdeclast  xmm3, xmm0              ; Perform the final decryption step
    retn

print:
    mov     eax,4                       ; Syscall number used to write
    mov     ebx,1                       ; File descriptor to write to (STDOUT)
    mov     ecx, output                 ; Text to write
    mov     edx,0x11                    ; Length of text to write
    int     0x80                        ; Call the syscall
    ret

exit:
    mov     eax, 0x01                   ; Syscall of exit
    mov     ebx, 0                      ; Return value
    int     0x80                        ; Call the syscall
    

section .rodata
    ; The array containing the keys in reverse order to the encryption routine
    rndkey: dq 0x76af4410293e28ca, 0xebcde711985307f0
            dq 0x5f916cdad1b1231d, 0x739ee0e1eefc43e0
            dq 0x8e204fc7adef890c, 0x9d62a301b16d2f3a
            dq 0x23cfc6cb4f9effe8, 0x2c0f8c3b3f4d60fd
            dq 0x6c513923fbe3d366, 0x1342ecc61c82a636
            dq 0x97b2ea4577956990, 0x0fc04af070d39f15
            dq 0xe02783d5ae471483, 0x7f13d5e5e7617550
            dq 0x4e6097567b01546b, 0x9872a0b50746f685
            dq 0x3561c33d7fda4cde, 0x9f345630492661d3
            dq 0x4abb8fe36e2c8546, 0xd61237e37c47a2ee
            dq 0x24970aa5b980796d, 0xaa55950d36fc2d0d
    ctxt:   dq 0x90385136801AFEF7, 0x54525E306D1134A0
```

This can be assembled with the following command:

```bash
$ nasm -f elf32 -o decr.o decr.s && ld -m elf_i386 -o decr decr.o && rm decr.o
$ ./decr
MiLiT4RyGr4d3MbR
```

This gives us the decrypted password. Entering this into the application performs the second round of encryption, which gives us the flag:

```
Password: MiLiT4RyGr4d3MbR

Wow, 512 bytes is a lot of space.
Enjoy the rest of AOTW!

Anyway, here's your flag: → AOTW{31oct__1s__25dec} ←

 - Retr0i
```

Given I had already extracted the encryption routine, it was trivial to save the keys as they were generated and then run the decryption routine based off of these saved keys. This file is located in [solve.s](asm/solver.s).

