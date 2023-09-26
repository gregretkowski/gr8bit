; Use to test X register addressing modes.

#include fibo.asm

#org 0x00
xindex:
        0x00
yindex:
        0x00

#org 0x8000
out:
#org 0xff00

string: 'Hello, World!', 0
mainprog:
        LDI 0x01
        STA xindex
        LDI 0x00
mainloop:
        STA yindex
        STA out
        LDA xindex
        ADD yindex
        STA xindex
        STA out       ; This is mem-mapped IO
        LDA yindex
        ADD xindex
        ; JC done     ; to loop the program switch this to mainloop
        JMP mainloop
done:
        HLT

#org 0xfffc
        JMP mainprog
