; fibo from ben eater sap1 adapted to my computer
; https://theshamblog.com/programs-and-more-commands-for-the-ben-eater-8-bit-breadboard-computer/
#org 0x00
xindex:
        0x00
yindex:
        0x00
#org 0x80
out:
#org 0xC0
mainprog:
       LDI 0x01
newloop:
       STA xindex
       ADD xindex
       STA yindex
       LDI 0x01
       LDA yindex
       STA out
       JMP newloop


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
        ; JC done        ; to loop the program switch this to mainloop
        JMP mainloop
done:
        HLT




#org 0xfc
        JMP mainprog
