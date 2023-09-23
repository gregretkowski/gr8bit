# opcodes

NOOP = 0b0 # No pins active, non-operation
HLT  = 0b1 << 0  # Halt the computer
CI   = 0b1 << 1  # PC Increment
PCLI = 0b1 << 2  # PC 'low' load from bus - SOON TO BE DEPRECATED
AI   = 0b1 << 3  # Accumulator load from bus
AO   = 0b1 << 4  # Accumulator write to bus
MRLI = 0b1 << 5  # Memory Register Low load from bus
ALUO = 0b1 << 6  # ALU Write to bus
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
PLLU = 0b001 << 18 # PC Low in from bus, unconditional
PLHU = 0b101 << 18 # PC Hi  in from bus, unconditional
PLLE = 0b010 << 18 # PC Low in from bus, On Equal
PLHE = 0b110 << 18 # PC Hi  in from bus, On Equal
PLLC = 0b011 << 18 # PC Low in from bus, On Carry
PLHC = 0b111 << 18 # PC Hi  in from bus, On Carry

FI   = 0b1 << 21 # Flag Register set from bus
FO   = 0b1 << 22 # Flag Register output to bus

# Following are not yet implemented - just reserving them
PCLO = 0b1 << 23  # PC 'low'  output to bus
PCHO = 0b1 << 24  # PC 'high' output to bus

SI   = 0b1 << 25 # Stack Register set from bus
SO   = 0b1 << 26 # Stack Register output to bus

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
        MSMR,
        MSMR|AI|MO|END
    ]],

    # 0010 aaaa   Put content of memory address aaaa into register B,
    # add A + B, store result in A.
    'ADD': [ 0x02, [
       MRLI|MO|CI,
        MSMR,
        MSMR|BI|MO,
        ALUO|AI|END     
    ]],
                  #             add A + B, store result in A.
#SUB   03  0011 aaaa   Put content of memory address aaaa into register B,
#                      substract A - B, store result in register A.
    #  0100 aaaa   Store contents of register A at memory address aaaa.   
    'STA': [ 0x04, [
        MRLI|MO|CI,
        MSMR,
        MSMR|MI|AO
    ]],
    # 0101 vvvv   Load 4 bit immediate value in register A (loads 'vvvv' in A).
    'LDI': [ 0x05, [
        AI|MO|CI,
    ]],
    # 0110 aaaa   Unconditional jump. Set program counter (PC) to aaaa,
    'JMP': [ 0x06, [
        PCLI|MO|CI
    ]], 
                  #    resume execution from that memory address.
    'JC':  [ 0x07, []],  # 0111 aaaa   Jump if carry. Set PC to aaaa when carry flag is set and resume 
                  #    from there. When carry flag is not set resume normally.
# JZ    08  1000 aaaa   Jump if zero. As above, but when zero flag is set.
# OUT   14  1110        Output register A to 7 segment LED display as decimal.
    # 1111        Halt execution.
    'HLT': [ 0x15, [HLT]],  
}

