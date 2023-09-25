# opcodes

'''
Control Lines - these map 1:1 with the control lines in Digital.
Used later to construct microcode for each opcode

'''
NOOP = 0b0 # No pins active, non-operation
HLT  = 0b1 << 0  # Halt the computer
CI   = 0b1 << 1  # PC Increment
PCLI = 0b1 << 2  # PC 'low' load from bus - DEPRECATED
AI   = 0b1 << 3  # Accumulator load from bus
AO   = 0b1 << 4  # Accumulator write to bus
MRLI = 0b1 << 5  # Memory Register Low load from bus
ALUO = 0b1 << 6  # ALU Write to bus - DEPRECATED (done via ALS*)
END  = 0b1 << 7  # END command, reset instruction step counter

MSPC = 0b00 << 8 # Program Counter selected for addr bus
MSMR = 0b01 << 8 # Full Mem register selected for addr bus
MSZP = 0b10 << 8 # MRL and value 0x00 high written to addr bus, Zero Page ops
MSSP = 0b11 << 8 # Stack Pointer low and value 0x01 high written to bus, Stack ops

IRI  = 0b1 << 10 # Instruction Register In from bus
MO   = 0b1 << 11 # Memory Out to bus
MI   = 0b1 << 12 # Memory read in from bus
BI   = 0b1 << 13 # B regster in from bus
BO   = 0b1 << 14 # B register out to bus

# ALS1,2,3
ALSU = 0b000 << 15 # ALU Unselected
ALSA = 0b001 << 15 # ALU Select Addition
ALSS = 0b010 << 15 # ALU Select Subtraction
ALSX = 0b011 << 15 # ALU Select X
ALSX = 0b100 << 15 # ALU Select X
ALSX = 0b101 << 15 # ALU Select X
ALSX = 0b110 << 15 # ALU Select X
ALSC = 0b111 << 15 # ALU Select Compare

# PCC1,2,3
PCUU = 0b000 << 18 # PC Counters Unselected
PCLU = 0b001 << 18 # PC Low in from bus, unconditional
PCHU = 0b101 << 18 # PC Hi  in from bus, unconditional
PCLE = 0b010 << 18 # PC Low in from bus, On Equal
PCHE = 0b110 << 18 # PC Hi  in from bus, On Equal
PCLC = 0b011 << 18 # PC Low in from bus, On Carry
PCHC = 0b111 << 18 # PC Hi  in from bus, On Carry

FI   = 0b1 << 21 # Flag Register set from bus
FC   = 0b1 << 22 # Flag Register clear
FO   = 0b1 << 23 # Flag Register output to bus

MRHI = 0b1 << 24  # Memory Register High load from bus

# Following are not yet implemented - just reserving them
PCLO = 0b1 << 25  # PC 'low'  output to bus
PCHO = 0b1 << 26  # PC 'high' output to bus

SPU  = 0b1 << 27 # Stack Register increment (up)
SPD  = 0b1 << 28 # Stack Register decrement
SPO  = 0b1 << 29 # Stack Register out to bus

# X Register
XI = 0b1 << 2
XO = 0b1 << 6
XU = 0b1 << 30
XD = 0b1 << 31

# One is unused!
# also could implement, if adding a bit: Neg, Ovf, various NOT's


# These are a matrix of 2x2

# The following drive the size and config of the control ROM
MAX_STEPS = 16 # could I reduce this to 8?? - 16 makes it 4 bits a nice round number
CONTROL_WORD_BYTES = 4 # 32 bits 
MAX_OPCODES = 32
BYTEORDER='little'

# ROM is 32 data bits by 12 address bits
# HIGH bits are opcodes
# LOW bits are steps of microcode

start_steps = [
    MSPC, # Program counter select RAM location
    IRI|MO|CI # Instruction In, Mem Out, Increment PC
]
end_steps = [
    END
]

opCodes = {
    'NOP': [ 0x00, [
    ]],
    # 0001 aaaa   Load contents of memory address aaaa into register A.
    'LDA': [ 0x01, [
        MRLI|MO|CI,
        MRHI|MO|CI,
        MSMR,
        MSMR|AI|MO|END
    ]],

    # Retr mem location into B reg, add A + B, store result in A.
    'ADD': [ 0x02, [
       MRLI|MO|CI,
       MRHI|MO|CI,
       MSMR,
       MSMR|BI|MO,
       ALSA|AI|END   
    ]],
    #SUB   03  0011 aaaa   Put content of memory address aaaa into register B,
    #                      substract A - B, store result in register A.
    # UNTESTED
    'SUB': [ 0x03, [
       MRLI|MO|CI,
       MRHI|MO|CI,
       MSMR,
       MSMR|BI|MO,
       ALSS|AI|END 
    ]],
    #  0100 aaaa   Store contents of register A at memory address aaaa.
    'STA': [ 0x04, [
        MRLI|MO|CI,
        MRHI|MO|CI,
        MSMR,
        MSMR|MI|AO|END
    ]],
    # 0101 vvvv   Load 4 bit immediate value in register A (loads 'vvvv' in A).
    'LDI': [ 0x05, [
        AI|MO|CI|END,
    ]],
    # 0110 aaaa   Unconditional jump. Set program counter (PC) to aaaa,
    'JMP': [ 0x06, [
        BI|MO|CI,
        PCHU|MO|CI,
        BO|PCLU|END
    ]], 
    # Compare A register with memory location - sets flags
    'CMP':  [ 0x08, [
        MRLI|MO|CI,
        MSMR,
        MSMR|BI|MO,
        ALSC|AI|END
    ]],
    # Branch if zero/equal flag set
    'BEQ':  [ 0x09, [
        BI|MO|CI,
        PCHE|MO|CI,
        BO|PCLE|END
    ]],
    # Clear/reset the flags register
    'CLF':  [ 0x0A, [
        FC|END
    ]],
    # Branch if carry flag set
    'BCS':  [ 0x07, [
        BI|MO|CI,
        PCHC|MO|CI,
        BO|PCLC|END
    ]],
    # STACK OPS - note stack pointer points at next available
    # memory location.
    # Push the accumulator onto the stack
    'PHA':  [ 0x0B, [
        SPO|MRLI,
        MSSP|MI|AO,
        SPU|END
    ]],
    # Pop from the stack into the accumulator
    'PLA':  [ 0x0C, [
        SPD,
        SPO|MRLI|MSSP,
        MSSP|AI|MO|END,
    ]],
    # jsr / rts jump to subroutine and return from subroutine ( stack stuff! )
    'JSR': [ 0x0D, [
        # push flags, low addr byte, high addr byte
        SPO|MRLI,           
        MSSP|FO|MI|SPU,
        SPO|MRLI,
        MSSP|PCLO|MI|SPU,
        SPO|MRLI,
        MSSP|PCHO|MI|SPU,
        # Now read in jump addrs & do the jump!
        # Now do the jump!
        BI|MO|CI,
        PCHU|MO|CI,
        BO|PCLU|END
    ]],
    'RTS': [ 0x0E, [
        # pull high addr byte, low addr byte, flags
        SPD,
        SPO|MRLI,
        PCHU|MO|SPD|MSSP,
        SPO|MRLI,
        PCLU|MO|SPD|MSSP,
        SPO|MRLI,
        FI|MO|MSSP, # This stack spot is now 'free' to be written to
        CI,         # Tick forward past the 2 addrs that held the jsr addr
        CI|END,     # We can then resume executing!
    ]],
    #
    # X Register operations - X used for indexed memory ops
    #
    'TAX': [ 0x10, [HLT]],
    'TXA': [ 0x11, [HLT]],
    'INX': [ 0x12, [HLT]],
    'DEX': [ 0x13, [HLT]],
    # Load/Store the Acc at memory indexed by X
    'LAX': [ 0x16, [HLT]],
    'SAX': [ 0x17, [HLT]],

    # Halt the computer    
    'HLT': [ 0x1F, [HLT]],
}

