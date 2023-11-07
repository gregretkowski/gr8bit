; monitor


; #ixnclude stdlib.asm

#org 0xF000
mainprog:


;  https://github.com/jefftranter/6502/blob/master/asm/wozmon/wozmon.s
;  The WOZ Monitor for the Apple 1
;  Written by Steve Wozniak in 1976


; Page 0 Variables

XAML            = 0x0024           ;  Last "opened" location Low
XAMH            = 0x0025           ;  Last "opened" location High
STL             = 0x0026           ;  Store address Low
STH             = 0x0027           ;  Store address High
L               = 0x0028           ;  Hex value parsing Low
H               = 0x0029           ;  Hex value parsing High
YSAV            = 0x002A           ;  Used to see if hex value is given
MODE            = 0x002B           ;  $00=XAM, $7F=STOR, $AE=BLOCK XAM
SCRATCH         = 0x0037           ; scratch for parsing hex digits

terminal        = 0x8001
keyready        = 0x8003
keyread         = 0x8002
sdisplay        = 0x8000
; Other Variables

IN              = 0x0200         ;  Input buffer to $027F

; NEGMASK           = 0x0035
; OVFMASK           = 0x0036
XTR               = 0x0041       ; Place to store X register when handling text buffer
XMR               = 0x0042       ; Place to store X register when handling memory locations

; These values, minus one! used in SETADR
L_M    = 0x0027
STL_M  = 0x0025
XAML_M = 0x0023




RESET:
                LDI 0b10000000
                TAX
                

; Handle text input
NOTCR:          CMP 8           ; Backspace?
                BEQ BACKSPACE   ; Yes.
                CMP 27          ; ESC?
                BEQ ESCAPE      ; Yes.
                INX             ; Advance text index.
                TXA
                CMP 0b10000001
                ; If this is our first time continue here TODO - otherwise
                ; we jump down to nextchar - Greg
                ; BPL NEXTCHAR  ; Auto ESC if > 127.
                BEQ ESCAPE
                JMP NEXTCHAR
ESCAPE:         LDI '\'         ; "\".
                JSR ECHO        ; Output it.
GETLINE:        LDI 10          ; CR.
                JSR ECHO        ; Output it.
                LDI 0x01        ; Initialize text index.
                TAX
BACKSPACE:      DEX             ; Back up text index.
                ; - BMI GETLINE     ; Beyond start of line, reinitialize.
                TFA
                ORA NEGMASK
                CMP 0b10000000
                BEQ GETLINE     ; Beyond start of line, reinitialize.
NEXTCHAR:       LDA keyready    ; Key ready?
                CMP 0x00
                BEQ NEXTCHAR    ; Loop until ready.
                LDA keyread     ; Load character. B7 should be ‘1’.
                SPX inbuf       ; Add to text buffer.
                JSR ECHO        ; Display character.
                CMP 10          ; CR?
                BEQ DONEINPUT   ; Yes.
                TXA
                STA sdisplay
                JMP NOTCR       ; No keep reading

; Drop though, got a CR! now we are processing the buffer

DONEINPUT:

; Setup
                LDI 0x00
                TAX

; Main stuff
                DEX
BLSKIP:         INX
NEXTITEM:
                LPX inbuf
                
                ; Code to check . / : / CR here!
                CMP 10          ; CR?
                BEQ GETLINE     ; Yes, done this line.
                CMP '.'         ; "."?
                BEQ SETM_BLOCK     ; Yes. Set STOR mode.
                CMP ':'         ; ":"?
                BEQ SETM_STOR     ; Yes. Set STOR mode.
                CMP 'R'         ; "R"?
                BEQ RUN         ; Yes. Run user program.
                
; convert from ascii string to binary/hex value
NEXTHEX:        ; LPX inbuf       ; Get character for hex test.
                XOR ASCIIZERO     ; Map digits to $0-9.
                CMP 0x0A        ; Digit?
                ; JMP DEBUG
                BCS NOT_DIGIT
                JMP DIG         ; Yes.
NOT_DIGIT:
                CLF
                ADD ASCIIAOFF     ; Map letter "A"-"F" to $FA-FF.
                BCS DIG           ; carry set, we can go to dig.
                ADD ASCIILCO
                ; TODO: If we arent a hexnumber we need to error out!!!
                ; the carry flag is unset if we are a valid digit
                ; This code doesnt seem to work shrug
                CMP 0x10
                BCS INVALID ; really we just start over/RESET
                

; Shift acc so that the value is the high bit
DIG:            CLF
                ASL
                ASL             ; Hex digit to MSD of A.
                ASL
                ASL
                ; JMP DEBUG


; shifts 4 chars into low/high byte - initial setup
                STX XTR         ; Switching X for loop counting, store Text index
                PHA
                LDI 0x03 ; Shift count.
                TAX
                PLA     
                CLF

; 4 times, shift 'scratch' into low, shift low into high.. 
HEXSHIFT:       ASL             ; Hex digit left, MSB to carry.
                STA SCRATCH

                LDA L
                ASL             ; Rotate into LSD.
                STA L
                LDA H
                ASL             ;  Rotate into MSD’s.
                STA H
                LDA SCRATCH
                DEX             ; Done 4 shifts?
                ;HLT
                BEQ X_BNE_HS
                JMP HEXSHIFT    ; No, loop.
X_BNE_HS:
; at the end, put out info on some display!!
                LDX XTR
                ; JMP BLSKIP ; going to read next char
                
                ; FALLTHOUGH - Code Continues.

                ; JMP DEBUG

; NOW we start doing stuff examine/store etc
                
                ; check 'store' bit, compared to mode.
                ; This is where we store a thing
                LDA MODE
                AND OVFMASK
                BEQ NOTSTOR
                LDA L           ; LSD’s of hex data.
                LDX XMR
                SPX STL         ; Store at current ‘store index’.
                LDX STL         ; Increment store index.
                INX
                STX STL
                BEQ X_BNE_NEXTI
                LDX XTR
                JMP NEXTITEM    ; Get next item. (no carry).            
X_BNE_NEXTI:
                LDX STH         ; Add carry to ‘store index’ high order.
                INX
                STX STH
                LDX XTR
TONEXTITEM:     JMP NEXTITEM    ; Get next command item.


RUN:            LDI 0x00        ; Run at current XAM index.
                TAX
                JPX XAML
NOTSTOR:    ; -  BMI XAMNEXT     ; B7=0 for XAM, 1 for BLOCK XAM.
                ; we continue below if we are in block-examine
                ; otherwise jump to XAMNEXT
                LDA MODE
                ORA MODE
                XOR MODE
                BEQ XAMNEXT
                LDI 0x02   ; setting x to 02 for to loop - then we access 
                TAX        ; Byte count.
                STX ???
                
SETADR:         LDX XMR
                LPX L_M       ; Copy hex data to
                SPX STL_M     ; ‘store index’.
                SPX XAML_M    ; And to ‘XAM index’.
                DEX             ; Next of 2 bytes.
                BEQ NXTPRNT
                JMP SETADR      ; Loop unless X=0.
NXTPRNT:        BEQ X_BNE_PRDATA
                JMP PRDATA      ; NE means no address to print.
X_BNE_PRDATA:
                LDA 10          ; CR.
                JSR ECHO        ; Output it.
                LDA XAMH        ; ‘Examine index’ high-order byte.
                JSR PRBYTE      ; Output it in hex format.
                LDA XAML        ; Low-order ‘examine index’ byte.
                JSR PRBYTE      ; Output it in hex format.
                LDA ':'         ; ":".
                JSR ECHO        ; Output it.
PRDATA:         LDA ' '         ; Blank.
                JSR ECHO        ; Output it.
                LPX XAML        ; Get data byte at ‘examine index’.
                JSR PRBYTE      ; Output it in hex format.
XAMNEXT:        STX MODE        ; 0->MODE (XAM mode).
                LDA XAML
                CMP L           ; Compare ‘examine index’ to hex data.
                LDA XAMH
;            --  SBC H  ; greg - this is doing some subtraction  to then cpompare, how can I rewrite it different?
                BCS TONEXTITEM  ; Not less, so no more data to output.
                LDA XAML
                ADD 0x01
                STA XAML
                BEQ NO_MOD8CHK   ; Increment ‘examine index’.
                JMP MOD8CHK
NO_MOD8CHK:
                LDA XAMH
                ADD 0x01
                STA XAMH
MOD8CHK:        LDA XAML        ; Check low-order ‘examine index’ byte
                AND 0x07        ; For MOD 8=0
                JMP NXTPRNT     ; Always taken.


SETM_BLOCK:
                LDA MODE
                AND NEGMASK
                STA MODE
                JMP BLSKIP

SETM_STOR:
                LDA MODE
                AND OVFMASK
                STA MODE
                JMP BLSKIP
                


; Functions to output to screen, incl conversion from value to ascii chars.
PRBYTE:         PHA             ; Save A for LSD.
                CLF             ; MSD to LSD position.
                ASR
                CLF
                ASR
                CLF
                ASR
                CLF
                ASR
                JSR PRHEX       ; Output hex digit.
                PLA             ; Restore A.
 
PRHEX:          AND 0x0F        ; Mask LSD for hex print.
                ADD '0'         ; Add "0". wut?
                CMP 'A'        ; Digit? wut?
                BCS ECHO        ; Yes, output it.
                ADD 0x06        ; Add offset for letter.

ECHO:           STA terminal
                RTS
INVALID:
                LDI 0xFA
DEBUG:
                STA sdisplay
                HLT

; Constants for math use.
ASCIIZERO: '0'
ASCIIAOFF: 0x99
ASCIILCO: 0x20
OVFMASK: 0b01000000 ; STOR
NEGMASK: 0b10000000 ; BLOCK
inbuf: 0x0200
ZEROTWO: 0x02


#org 0xfffc
        JMP mainprog

; %Run assembler.py monitor.asm 16k_rom.hex -s 0xc000 -l 16384


; BMI is branch if negative bit set. How to do a BMI:
; TFA
; ORA 0b10000000
; CMP 0b10000000
; BEQ (bmi branch)