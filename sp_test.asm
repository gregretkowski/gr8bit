; Stack Pointer testing code
; 
#org 0x20
xindex:
        0x00
yindex:
        0x00
#org 0xFF80
out:
#org 0xFFC0
mainloop:
        ; spop value into stack, then pull it back out
        LDA 0x42
        STA xindex
        PHA
        LDA 0x01
        PLA
        CMP xindex ; should be 42 again
        STA out
        
        ; Try jumping to a subroutine
        JSR subr
        ; should return here
        LDA 0x11
        STA out

        JMP mainloop ; done - repeat!
done:
        HLT ; shouldn't get here

subr:
        ; Our little subroutine - test if it works!
        LDA 0xAA
        STA out
        RTS
        HLT ; shouldn't get here either.

#org 0xfffc
        JMP mainloop
