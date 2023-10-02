; print a string to the terminal.

#include stdlib.asm

#org 0xFF00

keybuffer=0x1000

mainprog:

    LDI <string
    STA 0x0080
    LDI >string
    STA 0x0081
    JSR std_lineout
    LDI '>'
    STA terminal
    ; use a keybuffer at 0x1000
    LDI 0x00
    STA 0x0080
    LDI 0x10
    STA 0x0081
    JSR std_readline
    ; should be able to use the same addr and print it again!
    JSR std_lineout
    LDI '!'
    STA terminal
    HLT

string: 'Greetings, Professor Falken.', 10, 0

#org 0xfffc
        JMP mainprog