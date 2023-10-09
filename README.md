# GR 8bit Computer

This is an 8 bit CPU / computer inspired by the architecture of the 65xx MOS processor
family. It features an 8 bit data bus, 16 bit address space, a stack, an accumulator
register, index register, status flag register, and indirect/indexed memory operations.

The CPU is constrained to 32 control lines, and 32 instructions.

It is implemented with [Digital](https://github.com/hneemann/Digital)
The assembler and microcode generator require python

![screnshot](distribution/screenshot.png)

## Instruction Set

The following is the subsystems present in in the CPU,
the instructions related to the subsystem are detailed
out in each section.

Other vararies with the CPU - at coldstart the CPU
starts executing commands starting at address 
executing command starting at address 0xFFFC .
Typically you'd have a 'JMP mainprog' there.

The CPU starts paused - the man/auto button starts the
clock running. Alternatively you can manually step
via the tick button.

### Accumulator Register

The Accumulator (Acc) is the main register in the
computer. Most operations with data pass through the
accumulator.

LDI: Load an Immediate value into the Acc
LDA: Load a Value from a memory location into the Acc
STA: Store the value of the Acc into a memory location

### Arythmetic/Logic Unit & Flags Register

The ALU does all math and logic operations within the
CPU. ALU operations often set/alter the 'Flags'
register.

The flags register is 8 bits containing these flags:
NV0000ZC

N = Negative
V = Overflow - by convention, not set by CPU afaik
Z = Zero/Equal
C = Carry
0 = Undefined, can be user-defined

Flags get set on ALU ops, and on 'load' of the Acc/X registers.

TAF: Transfer Acc into the Flags Register
TFA: Transfer Flags Register into the Acc
CLF: Clear (zero out) the Flags Register

All relevant math ops are done with carry. So clear the flags
including carry via CLF if your flags are in an unknown state.

Results of all operations are written into the Accumulator.

ADD: Addition of the accumulator with a memory location plus carry bit.
AND: AND of the accumulator with a memory location
ORA: OR of the accumulator with a memory location
XOR: Exclusive OR of accumulator with memory location
ASL: Shift bits in the Acc left. Carry put into the rightmost bit.
ASR: Shift bits in the Acc right. Carry put into leftmost bit.

Subtraction is not in the ALU but can be accomplished via
twos-complement using XOR and ADD.

CMP: Compare the Accumulator to an immediate value. It mimics the
     6502 behavior setting the Neg, Zero, and Carry flag. If
     the values are equal Zero flag is set to '1'

### Flow Control and Stack

The CPU uses 2 8 bit registers to store the program counter
Low and High addresses. These registers are incremented as
the program progresses step-to-step. Several
operations can alter the program counter to implement
jumps to new addresses.

JMP: Jump to an address
BEQ: Branch if equal; jumps to an address if the Zero/Equal flag is set
BCS: Branch if carry; jumps to an address if the Carry flag is set
HLT: Halts the computer

The following ops use the stack; the stack is 256 bytes starting at
0x0010. If you are using the subroutine commands and the push/pop from
the stack be sure to leave the stack as you found it before returning
from your subroutine.

JSR: Jump to Subroutine. The current PC address is stored on the stack.
RTS: Return from Subroutine. Pulls the the PC address from the stack.

PHA: Push the Acc value onto the stack
PLA: Pop the current value on the stack into the Accumulator

### X Register

The X register serves as a secondary register and is
also used in indexed memory operations.

The X register can be loaded/stored in memory, copied
from the Accumulator, and incremented and decremented.
However it cannot be directly used for ALU ops.

LDX: Load X from value in a memory location
STX: Store value of X in a memory location
TAX: Transfer value of Acc into X
TXA: Transfer value of X into Acc
INX: Increment X
DEX: Decrement X

### Pointer/Indexed Memory Ops

These opcodes are dedicated to memory-indexed ops. They
operate on a memory location retrieved from 2 bytes of
memory - the opcode argument is the address of the LOW
byte of a memory address, and the next memory address
should contain the HIGH byte of the target memory
address.. This LLHH memory address is further added to
the current value in the X register to get the actual
address where a value is stored/retrived. It is a
combination of the indirect/indexed memory address
modes of the 6502.

If you just want the indirect address but not offset
by some value in X you must set X to zero.

LPX: Load the Acc with a value located at indirect/indexed memory
SPX: Store the Acc's value in an indirect/indexed memory location
JPX: Jump to the address stored in the indirect/indexed memory location

### Whats Not Implemented
Sticking to the constraint of 32 control lines and opcodes meant
leaving out many nice features of the 6502 - but fwict most of
these can be accomplished, just with extra code:

Math stuff: subtraction is omitted but this can be accomplished
with 2's complement and ADD/XOR. shift ops clear the carry flag
for ROL/ROR

Zero Page Operations: We just use full addresses to access ZP
locations. Just slower and more data bytes used.

Indirect/Indexed operations are combined in this CPU not separate
Omission of a Y register - you just have to store/load the
other two registers more frequently to shuffle data around instead
of having the convienence of another index register.
Theres no NOOP instruction just try to do something with minimal
side effects if you need it
Theres lots of other bit test and branch instructions, but you
can work around these. BCS, BEQ covers most cases, the flags
register can be manipulated in the accumulator, and
AND/ORA/CMP/BEQ can be used to mask out bits and do
conditional jumps based on those bits.
NMI/IRQ/BRK - not implemented!


## Files
* gr8bit_main.dig - Main file
* *.dig - supporting digital files
* assembler.py - assembler
* microcode_writer.py - generates miucrocode for CPU's sequencer
* opcodes.py - defines all the opcodes and microcode for the system
* *.hex various rom's needed for the system
* *.asm various assembler source files

## LICENSES

the assembler is based on another author's work - see license in the assembler file
the charmap.rom file is from https://pom1.sourceforge.net/?page=downloads and so that rom and other derivitives are GPLv2 licensed
All the rest here is my stuff and you can do with it what you will as long as you dont misrepresent me with whatever it is you do with it

## TODO

* Maybe some term/kbd bugs?
* Get wozmon ported over
* bug with tick, cold boot doesnt work if clock is not dead slow

## Other Notes

### CPU Flag Behaviors (design goal)

Note this means flags are (mostly!) set by the latest status of the latest register that is updated.

Z (bit 1)—Zero flag. This one's used a great deal, and basically the computer sets it when the result of any operation is zero. Load the X-register with $00, and you set the zero flag. Subtract $32 from $32, and you do the same. Many 6502 instructions affect the Z flag, and there's always a "zero or not-zero" aspect to it, but it's not always obvious to the novice when a zero condition exists. This is probably the most important of the flags, and if you master it, mastery of the others will be easy.

C (bit 0)—Carry flag. Carry is set whenever the accumulator rolls over from $FF to $00 (just like the odometer on a car, rolling over from all nines to all zeros). It's also set by various rotation and comparison instructions. The carry flag is about as important as the Z flag, and a little more mysterious, at least to me, but its operation is really rather simple.

N (bit 7)—Negative flag. (Some books call it S, for sign.) The N flag matches the high bit of the result of whatever operation the processor has just completed. If you load $FF (1111 1111) into the Y-register, for example, since the high bit of the Y-register is set, the N flag will be set, too. ML programmers make good use of the N flag. (By the way, even though this is the eighth bit, we call it bit 7, because computers start numbering things at 0.) In a computer technique called twos complement arithmetic, the high-order bit of a number is set to 1 if the number is negative, and cleared to 0 if it's positive, and that's where the N flag gets its name.

V (bit 6)—Overflow flag. This flag is important in twos complement arithmetic, but elsewhere it is rarely used. In the interest of simplicity, we'll say no more about it.
