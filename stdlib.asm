; standard library routines

; Input/Output Devices
sdout=0x8000
terminal=0x8001
keyready=0x8003
keyread=0x8002

#org 0xc000

std_lineout:
    ; prints a 0-terminated string to the terminal window.
    ; pass in L/H at mem addr 0080
    LDI 0x00
    TAX
std_lineout_loop:
    LPX 0x0080
    BEQ std_lineout_done
    STA terminal
    INX
    JMP std_lineout_loop
std_lineout_done:
    RTS

std_readline:
    ; Will read/echo keyboard input until a CR is encountered,
    ; and will store the null-terminated line in the indirect
    ; location specified in 0x0080
    LDI 0x00
    TAX
std_readline_poll:
    LDA keyready
    BEQ std_readline_poll
std_readline_keyread:
    LDA keyread
    STA terminal
    CMP 0x0a
    BEQ std_readline_done
    CMP 0x08
    BEQ std_readline_backspace
    SPX 0x0080
    INX
    JMP std_readline_poll
std_readline_backspace:
    DEX
    JMP std_readline_poll
std_readline_done:
    LDI 0x00
    SPX 0x0080
    RTS

