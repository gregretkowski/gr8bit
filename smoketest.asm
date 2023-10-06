; smoketest - this tests all the opcodes of the computer
;             it outputs numbers in order on the
;             status display. An indication of 'FA'
;             means a test failed. will display 'DD' after
;             all tests completed

keybuffer=0x1000
sdout=0x8000

#org 0xF000
mainprog:
    LDI 0x01
    STA sdout
    ; now test jump - we already know this works if we got this far
    JMP past_fail
    LDI 0xfa
    STA sdout
    HLT
past_fail:
     LDI 0x02
     STA sdout
; now try compare and jump on equal
     LDI 0x03
     STA 0x0001
     LDI 0x04
     LDA 0x0001
     CMP 0x03
     BEQ past_beq
     JMP fail
past_beq:
     STA sdout    
; test subroutine
     JSR test_jsr
     STA sdout
; test stack ops
    LDI 0x05
    PHA
    LDI 0xfa
    PLA
    STA sdout
 
; test X register Operations
    LDI 0x06
    TAX
    LDI 0xfa
    TXA
    STA sdout
    DEX
    INX
    INX
    TXA
    STA sdout

; test memory access pointer and x index (via x index?)
; LPX SPX
    ; put data in our target cell. 0x1008
    LDI 0x08
    STA 0x1008
    ; set up pointer - 0x1000 - and we will put data into 0x1008
lpx_pointer=0x1000
    LDI <lpx_pointer
    STA 0x0020
    LDI >lpx_pointer
    STA 0x0021
    ; set up X pointer
    LDI 0x08
    TAX
    LPX 0x0020
    ; STA sdout
    ; HLT
    CMP 0x08
    BEQ past_lpx
    JMP fail
past_lpx:
    STA sdout
; now try writing to a nearby address
    INX
    LDI 0x09
    SPX 0x0020
    LDA 0x1009
    CMP 0x09
    BEQ past_spx
    JMP fail
past_spx:
    STA sdout

; !!! test JPX opcode here!


; test BCS (Branch/Carry), clear flags, flags transfers

    LDA 0b0000001
    TAF
    BCS past_bcs
    JMP fail
past_bcs:
    LDI 0x10
    STA sdout
    LDI 0x00
    TFA
    ; STA sdout
    ; HLT
    ; note prev compare set the zero bit too. I guess thats a test too!
    CMP 0b00000011
    BEQ past_tfa
    JMP fail
past_tfa:
    LDI 0x11
    STA sdout
; test clear flags
    CLF
    TFA
    CMP 0x00
    BEQ past_clf
    JMP fail
past_clf:
    LDI 0x12
    STA sdout
    
;
; test ALU
;
    LDI 0x13
    CMP 0x03
    BEQ fail
    STA sdout
    
    ; ADD
    LDI 0x10
    STA 0x0001
    LDI 0x04
    CLF ; important!
    ADD 0x0001
    CMP 0x14
    ; STA sdout
    ; HLT
    BEQ past_add_nc
    JMP fail
past_add_nc:
    STA sdout
    
    ; test with carry
    LDA 0b0000001
    TAF
    LDI 0x04
    ADD 0x0001
    CMP 0x15
    BEQ past_add_c
    JMP fail
past_add_c:
    STA sdout
   

    ; AND
    LDI 0b00000001
    STA 0x0001
    LDI 0b00000011
    AND 0x0001
    CMP 0b00000001
    BEQ past_and
    JMP fail
past_and:
    LDI 0x16
    STA sdout

    ; ORA
    LDI 0b00000011
    STA 0x0001
    LDI 0b00000001
    ORA 0x0001
    CMP 0b00000011
    BEQ past_ora
    JMP fail
past_ora:
    LDI 0x17
    STA sdout

    ; XOR
    LDI 0b00000011
    STA 0x0001
    LDI 0b00000101
    XOR 0x0001
    CMP 0b00000110
    BEQ past_xor
    JMP fail
past_xor:
    LDI 0x18
    STA sdout

    ; ASL - no carry
    LDI 0b00000101
    CLF
    ASL
    CMP 0b00001010
    BEQ past_asl_nc
    JMP fail
past_asl_nc:
    LDI 0x19
    STA sdout

    ; ASL - carry
    LDI 0b00000101
    TAF
    ASL
    CMP 0b00001011
    BEQ past_asl_c
    JMP fail
past_asl_c:
    LDI 0x20
    STA sdout

    ; ASR - no carry
    LDI 0b00000100
    CLF
    ASR
    CMP 0b00000010
    BEQ past_asr_nc
    JMP fail
past_asr_nc:
    LDI 0x21
    STA sdout

    ; ASR - carry
    
    LDI 0b00000101
    TAF
    ASR
    CMP 0b10000010
    BEQ past_asr_c
    JMP fail
past_asr_c:
    LDI 0x22
    STA sdout

 
     LDI 0xdd
     STA sdout
     HLT ; halt after last test.    
test_jsr:
    LDI 0x04
    RTS
fail:
    LDI 0xfa
    STA sdout
    HLT


#org 0xfffc
        JMP mainprog

; %Run assembler.py smoketest.asm 16k_rom.hex -s 0xc000 -l 16384
