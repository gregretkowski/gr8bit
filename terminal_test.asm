; print a string to the terminal.

sdout=0x8000
terminal=0x8001
keyready=0x8003
keyread=0x8002

; #include stdlib.asm

;xindex_addr = 0x0020
; #org 0x8000
; out:

#org 0xFF00


mainprog:
    ; LDI 'x'
    ; CMP 'x'
    ; HLT
    ; LDI 0x01 ; 0x05 0x00
    ; LDI 0x00
    ; HLT ; 0x1F
    LDI 0x00
    TAX
mainloop:

    ; LDI 0x01       ; 0x05 0x00
    ; JMP mainloop
    ; BEQ mainloop   ; 0x09 0x00 0xff
    ; HLT            ; 0x1F
    
    LAX string
    BEQ mainloop_done
    STA terminal
    INX
    JMP mainloop
mainloop_done:
    JSR echo
    JMP mainprog

string: 'Greetings, Professor Falken.', 10, 0


; read from keyboard, echo to terminal
; BUG - one key is not read, but if you do twice quickly then the key is read and outputted
echo:
    ; LDI 0x01
    ; STA sdout
    LDA keyready ; check if there is a key to read, if not (0) then poll again
    BEQ echo
echo_keyread:
    ; LDA 0x02
    ; STA sdout
    LDA keyread
    ; BEQ echo_keyread  ; sometimes the first one is a 0!
    ; todo, add a done/escape key.
    STA sdout
    STA terminal
    CMP 0x0a
    BEQ echo_done
    JMP echo
echo_done:
    RTS

std_lineout:
    ; prints a 0-terminated string to the terminal window.
    ; pass in L/H at mem addr 0080
    LDA 0x00
    TAX
std_lineout_loop:
    LPX 0x0080
    BEQ std_lineout_done
    STA terminal
    INX
    JMP std_lineout_loop
std_lineout_done:
    RTS
    
    

#org 0xfffc
        JMP mainprog