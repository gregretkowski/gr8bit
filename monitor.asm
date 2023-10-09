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

terminal        = 0x8001
keyready        = 0x8003
keyread         = 0x8002
sdisplay        = 0x8000
; Other Variables

IN              = 0x0200         ;  Input buffer to $027F

inbuf             = 0x0030       ; pointer to the input buffer
inbufh            = 0x0031
NEGMASK           = 0x0035
XTR               = 0x0041       ; Place to store X register when handling text buffer
XMR               = 0x0042       ; Place to store X register when handling memory locations

; These values, minus one! used in SETADR
L_M    = 0x0027
STL_M  = 0x0025
XAML_M = 0x0023




RESET:
                LDI <IN
                STA inbuf
                LDI >IN
                STA inbufh
                LDI 0b10000000
                STA NEGMASK
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
                    
; Y reg is used as an index into the textstring we got
; X reg is used to interact with the mem location we are working with
; Acc is used for math scratch etc.

                LDI 0xFF        ; Reset text index.
                STA YSAV
                ; TAX
                LDA 0x00        ; For XAM mode.
                TAX             ; 0->X.
                ; todo are we mem reg or text reg here ^^^
SETSTOR:        ASL             ; Leaves $7B if setting STOR mode.
SETMODE:        STA MODE        ; $00=XAM $7B=STOR $AE=BLOK XAM
BLSKIP:         LDX XTR         ; Advance text index.
                INX
NEXTITEM:       LPX inbuf       ; Get character.
                CMP 10          ; CR?
                BEQ GETLINE     ; Yes, done this line.
                CMP '.'         ; "."?
                BCS X_BCC_BSK   ; Skip delimiter.
                JMP BLSKIP
X_BCC_BSK:
                BEQ SETMODE     ; Yes. Set STOR mode.
                CMP ':'         ; ":"?
                BEQ SETSTOR     ; Yes. Set STOR mode.
                CMP 'R'         ; "R"?
                BEQ RUN         ; Yes. Run user program.
                STX XTR
                LDX XMR
                STX L           ; $00-> L.
                STX H           ; and H.
                STX XMR
                LDX XTR
                STX YSAV        ; Save Y for comparison.
NEXTHEX:        LPX inbuf       ; Get character for hex test.
                XOR 0xB0        ; Map digits to $0-9.
                CMP 0x0A        ; Digit?
                BCS X_BCC_DIG
                JMP DIG         ; Yes.
X_BCC_DIG:
                ADD 0x88        ; Map letter "A"-"F" to $FA-FF.
                CMP 0xFA        ; Hex letter?
                BCS X_BCC_NOTHEX
                JMP NOTHEX      ; No, character not hex.
X_BCC_NOTHEX:
DIG:            ASL
                ASL             ; Hex digit to MSD of A.
                ASL
                ASL
                STX XTR
                LDX 0x04        ; Shift count. (?)
                
HEXSHIFT:       ASL             ; Hex digit left, MSB to carry.
                LDA L
                ASL             ; Rotate into LSD.
                STA L
                LDA H
                ASL             ;  Rotate into MSD’s.
                STA H
                DEX             ; Done 4 shifts?
                BEQ X_BNE_HS
                JMP HEXSHIFT    ; No, loop.
X_BNE_HS:
                STX XMR
                LDX XTR
                INX             ; Advance text index.
                BEQ X_BNE_NH
                JMP NEXTHEX     ; Always taken. Check next char for hex.
X_BNE_NH:
NOTHEX:         LDI 0x00        ; Check if L, H empty (no hex digits).
                CMP YSAV
                BEQ ESCAPE      ; Yes, generate ESC sequence.
;          -      BIT MODE        ; Test MODE byte.
;          -      BVC NOTSTOR     ;  B6=0 STOR 1 for XAM & BLOCK XAM
                LDA L           ; LSD’s of hex data.
                LDX XMR
                SPX STL         ; Store at current ‘store index’.
                LDX STL         ; Increment store index.
                INX
                STX STL
                BEQ X_BNE_NEXTI
                JMP NEXTITEM    ; Get next item. (no carry).
X_BNE_NEXTI:
                LDX STH         ; Add carry to ‘store index’ high order.
                INX
                STX STH
TONEXTITEM:     JMP NEXTITEM    ; Get next command item.
RUN:            LDI 0x00        ; Run at current XAM index.
                TAX
                JPX XAML
NOTSTOR:    ; -  BMI XAMNEXT     ; B7=0 for XAM, 1 for BLOCK XAM.
                LDX 0x02        ; Byte count.
                
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


#org 0xfffc
        JMP mainprog

; %Run assembler.py monitor.asm 16k_rom.hex -s 0xc000 -l 16384


; BMI is branch if negative bit set. How to do a BMI:
; TFA
; ORA 0b10000000
; CMP 0b10000000
; BEQ (bmi branch)