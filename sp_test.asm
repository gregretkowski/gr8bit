; Stack Pointer testing code
;
; #org 0x20
; xindex:
;         0x00
; yindex:
;        0x00

xindex=0x0020
yindex=0x0021
out=0x8000

#include stdlib.asm

;xindex_addr = 0x0020
; #org 0x8000
; out:

#org 0xFFC0
mainloop:
        ; spop value into stack, then pull it back out
        ; PHA:0B PLA:0C opcodes. 
        LDI 0x42 ; C0-C1
        STA xindex
        PHA ; C2
        LDI 0x01 ; C3-C4
        STA numeric_display ; C5-C7
        STA 0x8000
        PLA ; C8
        ; CMP xindex ; should be 42 again
        STA out ; C9-CB
        ; HLT ; CC
subtest:
        ; Try jumping to a subroutine
        JSR subr
        ; should return here
        LDI 0x11
        STA out
        HLT

        JMP mainloop ; done - repeat!
done:
        HLT ; shouldn't get here

subr:
        ; Our little subroutine - test if it works!
        LDI 0xAA
        STA out
        RWF
        HLT ; shouldn't get here either.

#org 0xfffc
        JMP subtest
