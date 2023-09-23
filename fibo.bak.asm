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
        STA xindex
        ADD xindex
        STA xindex
        ADD xindex
        STA xindex
        STA out

         LDI 0xff ; load ff into the reg
         STA out ; write to mem-mapped output
         HLT
          
        LDI 0x01
        STA xindex
mainloop:
        LDI 0x00
        STA yindex
        LDA xindex
        ADD yindex
        STA xindex
        STA out       ; This is mem-mapped IO
        LDA yindex
        ADD xindex
        JC done        ; to loop the program switch this to mainloop
        JMP mainloop
done:
        HLT




#org 0xfc
        JMP mainprog
