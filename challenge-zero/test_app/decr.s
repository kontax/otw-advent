global _start, main, a3_aes

section .bss
    buffer: resq 0x10

section .text

_start:
    mov     eax, 0x7d
    mov     ebx, _start
    mov     ecx, 0x1000
    mov     edx, 0x07
    int     0x80
    call    main

read_text:
    mov     eax, 0x3
    mov     ebx, 0x0
    mov     ecx, buffer
    mov     edx, 0x10
    int     0x80
    ret

main:
;    call    read_text
    movaps  xmm0, [keya]
    movaps  xmm3, [ctxt]
    call    a3_aes
    pxor    xmm3, [key0]
    ptest   xmm3, xmm3 
    jz      correct
    call    exit

    correct:
        mov     edx,0x10
        mov     ebx,1
        mov     eax,4
        int     0x80
        call    exit

a3_aes:
    pxor    xmm3, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key9]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key8]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key7]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key6]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key5]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key4]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key3]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key2]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key1]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0

    movaps  xmm0, [key0]
    ;aesimc  xmm0, xmm0
    aesdeclast  xmm3, xmm0

    retn

exit:
    mov     eax, 0x01
    mov     ebx, 0
    int     0x80
    

section .rodata
    key0:   dq 0x24970aa5b980796d, 0xaa55950d36fc2d0d
    key1:   dq 0x4abb8fe36e2c8546, 0xd61237e37c47a2ee
    key2:   dq 0x3561c33d7fda4cde, 0x9f345630492661d3
    key3:   dq 0x4e6097567b01546b, 0x9872a0b50746f685
    key4:   dq 0xe02783d5ae471483, 0x7f13d5e5e7617550
    key5:   dq 0x97b2ea4577956990, 0x0fc04af070d39f15
    key6:   dq 0x6c513923fbe3d366, 0x1342ecc61c82a636
    key7:   dq 0x23cfc6cb4f9effe8, 0x2c0f8c3b3f4d60fd
    key8:   dq 0x8e204fc7adef890c, 0x9d62a301b16d2f3a
    key9:   dq 0x5f916cdad1b1231d, 0x739ee0e1eefc43e0
    keya:   dq 0x76af4410293e28ca, 0xebcde711985307f0
    ctxt:   dq 0xe3ee1acf4a58913d, 0xb02923ca91d38d73
