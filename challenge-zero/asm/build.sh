nasm -f elf32 -o encr.o encr.s && ld -m elf_i386 -o encr encr.o && rm encr.o
nasm -f elf32 -o decr.o decr.s && ld -m elf_i386 -o decr decr.o && rm decr.o
nasm -f elf32 -o solve.o solve.s && ld -m elf_i386 -o solve solve.o && rm solve.o
