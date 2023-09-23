'''
Writes microcode for my little simulated pc

control word is 24 bytes
up to 16 steps per instruction

'''
from opcodes import opCodes, start_steps, end_steps, MAX_STEPS, CONTROL_WORD_BYTES, MAX_OPCODES
from helpers import hexdump, build_rom, write_rom


def build_sequence(opcode=None):
    if opcode:
        steps_code_nested = [start_steps, opCodes[opcode][1], end_steps]
        steps_code = [item for sub_list in steps_code_nested for item in sub_list]
    else:
        steps_code = []
    
    bytess = bytearray()
    for step in range(MAX_STEPS):
        if step < len(steps_code):
            print(steps_code[step])
            bytess += steps_code[step].to_bytes(CONTROL_WORD_BYTES, byteorder='little')
        else:
            x = 0
            bytess += x.to_bytes(CONTROL_WORD_BYTES, byteorder='little')
    return bytess


all_bytes = bytearray()
## Build a lookup for memory location to opcode
oc_lookup = {}
for ock, ocv in opCodes.items():
    oc_lookup[ocv[0]] = ock

#opCodes[opcode][1]
for oc in range(MAX_OPCODES):
    if oc in oc_lookup.keys():
        all_bytes += build_sequence(oc_lookup[oc])
    else:
        all_bytes += build_sequence()

#my_data = build_sequence('LDA')
print(hexdump(all_bytes))
print
print(f"ROM Length: {len(all_bytes)}")
print
print(build_rom(all_bytes,4))
write_rom('microcode.hex',all_bytes,4)
