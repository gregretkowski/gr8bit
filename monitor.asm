; monitor


#include stdlib.asm

#org 0xF000
mainprog:


;  https://github.com/jefftranter/6502/blob/master/asm/wozmon/wozmon.s
;  The WOZ Monitor for the Apple 1
;  Written by Steve Wozniak in 1976


; Page 0 Variables

XAML            = 0x24           ;  Last "opened" location Low
XAMH            = 0x25           ;  Last "opened" location High
STL             = 0x26           ;  Store address Low
STH             = 0x27           ;  Store address High
L               = 0x28           ;  Hex value parsing Low
H               = 0x29           ;  Hex value parsing High
YSAV            = 0x2A           ;  Used to see if hex value is given
MODE            = 0x2B           ;  $00=XAM, $7F=STOR, $AE=BLOCK XAM

terminal        = 0x8001
keyready        = 0x8003
keyread         = 0x8002
; Other Variables

IN              = 0x0200         ;  Input buffer to $027F

inbuf             = 0x0030         ; pointer to the input buffer
inbufh            = 0x0031


RESET:
                LDI <IN
                STA inbuf
                LDI >IN
                STA inbufh
                

; Handle text input
NOTCR:          CMP 8          ; Backspace?
                BEQ BACKSPACE   ; Yes.
                CMP 27          ; ESC?
                BEQ ESCAPE      ; Yes.
                INX             ; Advance text index.
                ; BPL NEXTCHAR    ; Auto ESC if > 127.
ESCAPE:         LDI '\'    ; "\".
                JSR ECHO        ; Output it.
GETLINE:        LDI '\n'        ; CR.
                JSR ECHO        ; Output it.
                LDI 0x01        ; Initialize text index.
                TAX
BACKSPACE:      DEX             ; Back up text index.
                ; BMI GETLINE     ; Beyond start of line, reinitialize.
NEXTCHAR:       LDA keyready    ; Key ready?
                CMP 0x00
                BEQ NEXTCHAR    ; Loop until ready.
                LDA keyread     ; Load character. B7 should be ‘1’.
                SPX inbuf       ; Add to text buffer.
                JSR ECHO        ; Display character.
                CMP '\n'        ; CR?
                BEQ DONEINPUT   ; Yes.
                JMP NOTCR       ; No keep reading

; Drop though, got a CR! now we are processing the buffer
DONEINPUT:

                LDI 0xFF        ; Reset text index.
                TAX
                LDA 0x00        ; For XAM mode.
                TAX             ; 0->X.
SETSTOR:        ASL             ; Leaves $7B if setting STOR mode.
SETMODE:        STA MODE        ; $00=XAM $7B=STOR $AE=BLOK XAM
BLSKIP:         INY             ; Advance text index.
NEXTITEM:       LDA IN,Y        ; Get character.
                CMP #$8D        ; CR?
                BEQ GETLINE     ; Yes, done this line.
                CMP #'.'+$80    ; "."?
                BCC BLSKIP      ; Skip delimiter.
                BEQ SETMODE     ; Yes. Set STOR mode.
                CMP #':'+$80    ; ":"?
                BEQ SETSTOR     ; Yes. Set STOR mode.
                CMP #'R'+$80    ; "R"?
                BEQ RUN         ; Yes. Run user program.
                STX L           ; $00-> L.
                STX H           ; and H.
                STY YSAV        ; Save Y for comparison.
NEXTHEX:        LDA IN,Y        ; Get character for hex test.
                EOR #$B0        ; Map digits to $0-9.
                CMP #$0A        ; Digit?
                BCC DIG         ; Yes.
                ADC #$88        ; Map letter "A"-"F" to $FA-FF.
                CMP #$FA        ; Hex letter?
                BCC NOTHEX      ; No, character not hex.
DIG:            ASL
                ASL             ; Hex digit to MSD of A.
                ASL
                ASL
                LDX #$04        ; Shift count.
HEXSHIFT:       ASL             ; Hex digit left, MSB to carry.
                ROL L           ; Rotate into LSD.
                ROL H           ;  Rotate into MSD’s.
                DEX             ; Done 4 shifts?
                BNE HEXSHIFT    ; No, loop.
                INY             ; Advance text index.
                BNE NEXTHEX     ; Always taken. Check next char for hex.
NOTHEX:         CPY YSAV        ; Check if L, H empty (no hex digits).
                BEQ ESCAPE      ; Yes, generate ESC sequence.
                BIT MODE        ; Test MODE byte.
                BVC NOTSTOR     ;  B6=0 STOR 1 for XAM & BLOCK XAM
                LDA L           ; LSD’s of hex data.
                STA (STL,X)     ; Store at current ‘store index’.
                INC STL         ; Increment store index.
                BNE NEXTITEM    ; Get next item. (no carry).
                INC STH         ; Add carry to ‘store index’ high order.
TONEXTITEM:     JMP NEXTITEM    ; Get next command item.
RUN:            LDI 0x00        ; Run at current XAM index.
                TAX
                JPX XAML
NOTSTOR:        BMI XAMNEXT     ; B7=0 for XAM, 1 for BLOCK XAM.
                LDX #$02        ; Byte count.
SETADR:         LDA L-1,X       ; Copy hex data to
                STA STL-1,X     ; ‘store index’.
                STA XAML-1,X    ; And to ‘XAM index’.
                DEX             ; Next of 2 bytes.
                BNE SETADR      ; Loop unless X=0.
NXTPRNT:        BNE PRDATA      ; NE means no address to print.
                LDA #$8D        ; CR.
                JSR ECHO        ; Output it.
                LDA XAMH        ; ‘Examine index’ high-order byte.
                JSR PRBYTE      ; Output it in hex format.
                LDA XAML        ; Low-order ‘examine index’ byte.
                JSR PRBYTE      ; Output it in hex format.
                LDA #':'+$80    ; ":".
                JSR ECHO        ; Output it.
PRDATA:         LDA #$A0        ; Blank.
                JSR ECHO        ; Output it.
                LDA (XAML,X)    ; Get data byte at ‘examine index’.
                JSR PRBYTE      ; Output it in hex format.
XAMNEXT:        STX MODE        ; 0->MODE (XAM mode).
                LDA XAML
                CMP L           ; Compare ‘examine index’ to hex data.
                LDA XAMH
                SBC H
                BCS TONEXTITEM  ; Not less, so no more data to output.
                INC XAML
                BNE MOD8CHK     ; Increment ‘examine index’.
                INC XAMH
MOD8CHK:        LDA XAML        ; Check low-order ‘examine index’ byte
                AND #$07        ; For MOD 8=0
                BPL NXTPRNT     ; Always taken.

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