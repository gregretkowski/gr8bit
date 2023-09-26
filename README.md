# GR 8bit Computer

This is an 8 bit computer implemented with [Digital](https://github.com/hneemann/Digital)
The assembler and microcode generator require python

![screnshot](distribution/screenshot.png)

## Files
* gr8bit_main.dig - Main file
* *.dig - supporting digital files
* assembler.py - assembler
* microcode_writer.py - generates miucrocode for CPU's sequencer
* opcodes.py - defines all the opcodes and microcode for the system
* *.hex various rom's needed for the system


## TODO

* verify X reg operations and indexed memory
* switch zp addr mode to x-indexed mode
* update assembler syntax to turbo
* ensure flags are updated as-spec'ed for reg ops (eq/z set on inx rollover)

* Hook up a terminal (keyboard/mouse)
* Get wozmon ported over
* get remaining ALU (bit/logic) ops working

* get a 'basic' working
* hook up some 'graphical display'

## Other Notes

### CPU Flag Behaviors (design goal)

Note this means flags are (mostly!) set by the latest status of the latest register that is updated.

Z (bit 1)—Zero flag. This one's used a great deal, and basically the computer sets it when the result of any operation is zero. Load the X-register with $00, and you set the zero flag. Subtract $32 from $32, and you do the same. Many 6502 instructions affect the Z flag, and there's always a "zero or not-zero" aspect to it, but it's not always obvious to the novice when a zero condition exists. This is probably the most important of the flags, and if you master it, mastery of the others will be easy.

C (bit 0)—Carry flag. Carry is set whenever the accumulator rolls over from $FF to $00 (just like the odometer on a car, rolling over from all nines to all zeros). It's also set by various rotation and comparison instructions. The carry flag is about as important as the Z flag, and a little more mysterious, at least to me, but its operation is really rather simple.

N (bit 7)—Negative flag. (Some books call it S, for sign.) The N flag matches the high bit of the result of whatever operation the processor has just completed. If you load $FF (1111 1111) into the Y-register, for example, since the high bit of the Y-register is set, the N flag will be set, too. ML programmers make good use of the N flag. (By the way, even though this is the eighth bit, we call it bit 7, because computers start numbering things at 0.) In a computer technique called twos complement arithmetic, the high-order bit of a number is set to 1 if the number is negative, and cleared to 0 if it's positive, and that's where the N flag gets its name.

V (bit 6)—Overflow flag. This flag is important in twos complement arithmetic, but elsewhere it is rarely used. In the interest of simplicity, we'll say no more about it.
