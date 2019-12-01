global _start, main

section .bss
    rndkey: resq 0xb0
    output: resq 0x11

section .text

_start:
    call    _mprotect
    call    main

; Allow the text section to be writable
_mprotect:
    mov     eax, 0x7d
    mov     ebx, _start
    mov     ecx, 0x1000
    mov     edx, 0x07
    int     0x80
    ret

print:
    mov     edx,0x11
    mov     ebx,1
    mov     ecx, output
    mov     eax,4
    int     0x80
    call    exit

main:
   ; Call encryption on random string to get round keys
    movaps  xmm0, [key]
    movaps  xmm3, [test]

    ; Store the keys for later use
    mov     ecx, rndkey
    movdqu  [ecx], xmm0
    add     ecx, 0x10
    call    encrypt

    ; Use round keys to decrypt ciphertext, going backwards
    sub     ecx, 0x10
    movaps  xmm3, [ctxt]
    movaps  xmm0, [ecx]
    pxor    xmm3, xmm0
    call    decrypt

    ; Print the result to screen with a newline
    movaps  [output], xmm3
    mov     [output+0x10], byte 0xa
    call    print
    call    exit

decrypt:
    
    ; Loop through each round key backwards until the initial one
    sub     ecx, 0x10
    movaps  xmm0, [ecx]
    aesimc  xmm0, xmm0
    aesdec  xmm3, xmm0
    cmp     ecx, rndkey+0x10
    jnz     decrypt

    ; Call the aesdeclast on the original key to get the plaintext
    sub     ecx, 0x10
    movaps  xmm0, [ecx]
    aesdeclast  xmm3, xmm0
    retn
    

encrypt:
    pxor    xmm2, xmm2
    pxor    xmm3, xmm0
    mov     bx, 0x36E5
    mov     ah, 0x73
    
    loc_7CB0:
        shr     ax, 7
        div     bl
        mov     byte [loc_7CB9+5], ah
        
    loc_7CB9:
        aeskeygenassist xmm1, xmm0, 0x45
        pshufd  xmm1, xmm1, 0xFF
        
    loc_7CC4:
        shufps  xmm2, xmm0, 0x10
        pxor    xmm0, xmm2
        xor     byte byte [loc_7CC4+3], 0x9C
        js      short loc_7CC4

        pxor    xmm0, xmm1
        ; Store the key for decryption
        movdqu  [ecx], xmm0
        add     ecx, 0x10
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

    ; Inital key
    key:    dq 0x24970aa5b980796d, 0xaa55950d36fc2d0d

    ; Text to encrypt for calculating round keys
    test:   dq 0x4141414141414141, 0x4141414141414141

    ; Ciphertext to decrypt
    ctxt:   dq 0x90385136801AFEF7, 0x54525E306D1134A0
