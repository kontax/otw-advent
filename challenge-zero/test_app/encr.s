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
    movaps  xmm0, [key]
    movaps  xmm3, [val]
    call    a3_aes
    pxor    xmm3, [tst]
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
    pxor    xmm2, xmm2
    pxor    xmm3, xmm0
    mov     bx, 0x36E5
    mov     ah, 0x73
    
    loc_7CB0:
        shr     ax, 7
        div     bl
        mov     byte [loc_7CB9+5], ah
        
    loc_7CB9:
        aeskeygenassist xmm1, xmm0, 0x1
        pshufd  xmm1, xmm1, 0xFF
        
    loc_7CC4:
        shufps  xmm2, xmm0, 0x10
        pxor    xmm0, xmm2
        xor     byte byte [loc_7CC4+3], 0x9C
        js      short loc_7CC4

        pxor    xmm0, xmm1
        cmp     ah, bh
        jz      short loc_7CE2
        aesenc  xmm3, xmm0
        jmp     short loc_7CB0

    loc_7CE2:
         aesenclast xmm3, xmm0
         retn

exit:
    mov     eax, 0x01
    mov     ebx, 0
    int     0x80
    

section .rodata
    key:    dd 0xb980796d
            dd 0x24970aa5
            dd 0x36fc2d0d
            dd 0xaa55950d

    val:    dd 0x41414141
            dd 0x41414141
            dd 0x41414141
            dd 0x41414141

    tst:    dd 0x54525E30
            dd 0x6D1134A0
            dd 0x90385136
            dd 0x801AFEF7

    ptx:    dd 0xc855cc37
            dd 0xc06a5cb9
            dd 0xace8d355
            dd 0x79900c6e

