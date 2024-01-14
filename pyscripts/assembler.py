#

'''
TODO:

Any way to validate opcode argument length???
> amd < syntax doesnt work with variables

IF I need it - support expressions, ex
   0x00+0x01, labelfoo+0b00000001

IF I want to switch to turbo syntax
  http://turbo.style64.org/docs/turbo-macro-pro-tmpx-syntax
  $ (hex) % (bin) 'a' (string text)
  *=
  .byte .word (word gets little indian'ed)
  .text .null
  label = $1234
  .include "helpers.asm"
  ? .binary "some.bin"
  $20 + 4  (expressions)
   <>! (select low or high byte of word)
  

'''
# ITs a bug, but it currently does not honor any of this and
# addresses have an extra 00 - which is a NOOP so its prolly okish
eight_bit_addresses = False
little_indian = True

'''
Sample code listing


start:
            LDI <string   ; do stuff
            PHS
            LDI >string   ; do other stuff
            BEQ start
    
string:    'Hello, World!', 10, 0
ptr:       0x0000

'''
# > is rather universal for the high byte while
# < selects the low byte.

# https://www.youtube.com/watch?v=rdKX9hzA2lU

from opcodes import opCodes, BYTEORDER
from helpers import hexdump, build_rom, write_rom
import sys, argparse

#lines, lineinfo, lineadr, labels = [], [], [], {}

class Gr8Assembler:
    def __init__(self):
        pass

    # Recursively read in files, supporting '#include' directive
    #
    def recursive_file_read(self,filename):
        lines = []
        line_ids = []
        i = 0
        try: f = open(filename, 'r')
        except: print("ERROR: Can't find file \'"+filename+"\'."); exit(1)
        while True:
            line = f.readline()
            if not line: break # EOF
            i+=1
            line_stripped = line.strip()
            line_id = f"{filename} line {i}"
            
            # BUG/FIXME: commenting out '#include' still includes the file!
            # this is a bug.
            k = line.find('#include')
            if k != -1:                                 # interpret anything after #include as a filename
                line = line[k+8:].strip().replace('\"', '').replace('\'', '')
                f_lines, f_line_ids = self.recursive_file_read(line)                        # read include files recursively
                lines.extend(f_lines)
                line_ids.extend(f_line_ids)
            else:
                lines.append(line_stripped)
                line_ids.append(line_id)
        f.close()
        return lines, line_ids


    def tokenize_line(self,line_string):
        ''' returns an array of numbers - fixes byte order '''
        line_string = line_string.replace(',', ' ')
        tokens = line_string.split()
        results = []
        for idx,x in enumerate(tokens):
            if x.find('0x') == 0:
                # Bug doesnt handle odd numbers beyond 1.
                just_numbers = tokens[idx][2:]
                #split_tokens = [int("0x"+just_numbers[i:i+2],0) for i in range(0, len(just_numbers), 2)]
                split_tokens = [("0x"+just_numbers[i:i+2]) for i in range(0, len(just_numbers), 2)]
                split_tokens.reverse()
                for t in split_tokens:
                    results.append(t)
            else:
                results.append(int(x,0))
        return results

    def parse_lines(self,lines,line_ids):
        # This function derived from:
        # https://github.com/slu4coder/Minimal-UART-CPU-System/blob/main/Python%20Assembler/asm.py
        # -------------------------------------------------------------------------------
        # Minimal Assembler for the 'MINIMAL CPU System' Revision 1.3 and higher
        # Copyright (c) 2021, 2022 Carsten Herting (slu4)
        # -------------------------------------------------------------------------------
        # MIT LICENSE
        # Permission is hereby granted, free of charge, to any person obtaining a copy of
        # this software and associated  documentation files  (the "Software"), to deal in
        # the Software without  restriction, including  without  limitation the rights to
        # use, copy,  modify, merge, publish, distribute, sublicense,  and/or sell copies
        # of the Software, and  to permit persons to whom the Software is furnished to do
        # so, subject to the following conditions:
        # The above copyright notice and  this permission notice shall be included in all
        # copies or substantial portions of the Software.
        # THE  SOFTWARE  IS PROVIDED "AS IS",  WITHOUT  WARRANTY OF  ANY KIND, EXPRESS OR
        # IMPLIED,  INCLUDING  BUT  NOT  LIMITED  TO  THE  WARRANTIES OF MERCHANTABILITY,
        # FITNESS FOR  A PARTICULAR  PURPOSE AND  NONINFRINGEMENT. IN NO  EVENT SHALL THE
        # AUTHORS  OR  COPYRIGHT  HOLDERS  BE  LIABLE FOR  ANY  CLAIM, DAMAGES  OR  OTHER
        # LIABILITY,  WHETHER IN AN ACTION  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        # OUT OF OR IN  CONNECTION WITH  THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        # SOFTWARE.
        # -------------------------------------------------------------------------------
        lineinfo, lineadr, labels, var_labels = [], [], {}, {}
        LINEINFO_NONE, LINEINFO_ORG, LINEINFO_BEGIN, LINEINFO_END = 0x00000, 0x10000, 0x20000, 0x40000
        #
        #
        # PASS 1
        #
        for i in range(len(lines)):                         # PASS 1: do PER LINE replacements
            while(lines[i].find('\'') != -1):               # replace '...' occurances with corresponding ASCII code(s)
                k = lines[i].find('\'')
                l = lines[i].find('\'', k+1)
                if k != -1 and l != -1:
                    replaced = ''
                    for c in lines[i][k+1:l]: replaced += str(ord(c)) + ' '
                    lines[i] = lines[i][0:k] + replaced + lines[i][l+1:]
                else: break

            if (lines[i].find(';') != -1): lines[i] = lines[i][0:lines[i].find(';')]    # delete comments
            lines[i] = lines[i].replace(',', ' ')                                       # replace commas with spaces

            lineinfo.append(LINEINFO_NONE)                  # generate a separate lineinfo
            if lines[i].find('#begin') != -1:
                lineinfo[i] |= LINEINFO_BEGIN
                lines[i] = lines[i].replace('#begin', '')
            if lines[i].find('#end') != -1:
                lineinfo[i] |= LINEINFO_END
                lines[i] = lines[i].replace('#end', '')
            k = lines[i].find('#org')
            if (k != -1):        
                s = lines[i][k:].split(); rest = ""         # split from #org onwards
                lineinfo[i] |= LINEINFO_ORG + int(s[1], 0)  # use element after #org as origin address
                for el in s[2:]: rest += " " + el
                lines[i] = (lines[i][0:k] + rest).strip()   # join everything before and after the #org ... statement

            if lines[i].find(':') != -1:
                # Give it a special name!
                label_name = "@@addr_" + lines[i][:lines[i].find(':')]
                #labels[label_name] = i   # put label with it's line number into dictionary
                labels[label_name] = [i, '0x@@']
                lines[i] = lines[i][lines[i].find(':')+1:]  # cut out the label

            # Handle value assignment of labels things with '=' are labels that are constants!
            k = lines[i].find('=')
            if (k != -1):
                var_label  = lines[i][:k].strip()
                value_str =  lines[i][k+1:].strip()

                labels[var_label] = self.tokenize_line(value_str)
                # Must remove this line from the listing. yah?
                lines[i] = ""


            lines[i] = lines[i].split()                     # now split line into list of bytes (omitting whitepaces)

            for j in range(len(lines[i])-1, -1, -1):        # iterate from back to front while inserting stuff
                #if "0x0302" == lines[i][j]:
                #    print(lines[i][j])
                #    raise("found the val!")
                old_line = lines[i]
                #print(f"Looking at '{old_line}' on line {i+1} token {j+1}")
                try:
                    #old_line = lines[i][j]
                    #print(opCodes.keys())
                    lines[i][j] = str(opCodes[lines[i][j]][0])     # try replacing mnemonic with opcode
                    #print(f"Found opcode '{old_line}' on line {i+1}")
                except: 
                    if lines[i][j].find('0x') == 0 and len(lines[i][j]) > 4:    # replace '0xWORD' with 'LSB MSB'
                        val = int(lines[i][j], 16)
                        # strip out the LSB, make it the value in the current list index.
                        lines[i][j] = str(val & 0xff)
                        # Insert the next value of a 2-byte string - in a new location in the list of lines.
                        lines[i].insert(j+1, str((val>>8) & 0xff))
                    #elif lines[i][j].find('0b') == 0 and len(lines[i][j]) > 4:

        #
        # PASS 2
        #
        adr = 0                                             # PASS 2: default start address
        for i in range(len(lines)):
            for j in range(len(lines[i])-1, -1, -1):        # iterate from back to front while inserting stuff
                e = lines[i][j]
                #print(f"{i}:{j}")
                #print(e)
                if isinstance(e, str):
                    if e[0] == '<' or e[0] == '>' : continue    # only one byte is required for this label
                    if e.find('+') != -1: e = e[0:e.find('+')]  # omit +/- expressions after a label
                    if e.find('-') != -1: e = e[0:e.find('-')]
                try:
                    if "@@addr_"+e in labels.keys():
                        e = "@@addr_"+e
                    # is this element a label? add placeholders for any bits.
                    labels[e]
                    # is this element a label? => add a placeholder for any extra elements like MSB
                    for x in range(len(labels[e])-1):
                        lines[i].insert(j+1+x, '0x@@')
                except: pass
            if lineinfo[i] & LINEINFO_ORG: adr = lineinfo[i] & 0xffff   # react to #org by resetting the address
            lineadr.append(adr);                            # save line start address
            adr += len(lines[i])                            # advance address by number of (byte) elements

        for l in labels:
            #print(f"Processing label {l}")
            if l.find("@@addr_") != -1:
                labels[l] = lineadr[labels[l][0]] # update label dictionary from 'line number' to 'address'
                #print(f"{l} -> {labels[l]}")
        #
        # PASS 3
        #
        for i in range(len(lines)):                         # PASS 3: replace 'reference + placeholder' with 'MSB LSB'
            for j in range(len(lines[i])):
                e = lines[i][j]; pre = ''; off = 0
                if isinstance(e, str):
                    if e[0] == '<' or e[0] == '>': pre = e[0]; e = e[1:]
                    if e.find('+') != -1: off += int(e[e.find('+')+1:], 0); e = e[0:e.find('+')]
                    if e.find('-') != -1: off -= int(e[e.find('-')+1:], 0); e = e[0:e.find('-')]
                #print(f"trying label for {e}")
                try:
                    #print(f"trying label for {e}")
                    if "@@addr_"+e in labels.keys():
                        e = "@@addr_"+e
                    #if e.find("@@addr_") != -1: # This is an address label.
                        adr = labels[e] + off
                        #print(f"Processing label {e} values {labels[e]}")
                        if pre == '<': lines[i][j] = str(adr & 0xff)
                        elif pre == '>': lines[i][j] = str((adr>>8) & 0xff)
                        else:
                            lines[i][j] = str(adr & 0xff)
                            #if eight_bit_addresses:
                            #    del lines[i][j+1]
                            #    j+=1
                            #else:
                            lines[i][j+1] = str((adr>>8) & 0xff)
                    elif e in labels.keys(): # its a constant/variable label
                        # > is rather universal for the high byte
                        if pre == '<' and len(labels[e]) == 2:
                            lines[i][j] = labels[e][0]
                            #lines[i][j] = str(adr & 0xff)
                            
                        elif pre == '>' and len(labels[e]) == 2:
                            #lines[i][j] = str((adr>>8) & 0xff)
                            lines[i][j] = labels[e][1]
                        else:
                            for x in range(len(labels[e])):
                                lines[i][j+x] = labels[e][x]
                except: pass
                try: isinstance(lines[i][j], str) and int(lines[i][j], 0)                    # check if ALL elements are numeric
                except:
                    print('ERROR in ' + line_ids[i] + ': Undefined expression \'' + lines[i][j] + '\'')
                    #print(line_ids[i])
                    exit(1)


        insert = ''; showout = True                         # print out 16 data bytes per row in Minimal's 'cut & paste' format
        for i in range(len(lines)):
            if lineinfo[i] & LINEINFO_BEGIN: showout = True
            if lineinfo[i] & LINEINFO_END: showout = False
            if showout:
                if lineinfo[i] & LINEINFO_ORG:
                    if insert: print(':' + insert); insert = ''
                    print('%04.4x' % (lineinfo[i] & 0xffff))
                for e in lines[i]:
                    #print(f"{e} {e.__class__}")
                    try:
                        insert += ('%02.2x' % (int(e, 0) & 0xff)) + ' '
                    except:
                        print(f"Failed to do {e}")
                        raise
                    if len(insert) >= 16*3 - 1: print(':' + insert); insert = ''
        if insert: print(':' + insert)

        if len(sys.argv) > 2:                               # print out all (matching) label definitions and their addresses
            k = sys.argv[2].find('-s') 
            if k != -1:
                sym = sys.argv[2][k+2:]
                for key, value in labels.items():
                    if key.find(sym) != -1:
                        print('#org '+ '%04.4x' % (value & 0xffff) + '\t' + key + ':')

        return(lineinfo,lineadr,lines)


    def make_mem_struct(self,line_addrs,my_lines):
        ''' This creates a dict with addresses->values pairs. Used later to fill
            out the contents of the ROM
        '''
        mem_struct = {}
        # Take each lineaddr/lines combo and convert to an address with a byte
        for idx, x in enumerate(line_addrs):
            my_addr = line_addrs[idx]
            for str_byte in my_lines[idx]:
                #print(str_byte)
                mem_struct[my_addr] = int(str_byte,0).to_bytes(1, byteorder=BYTEORDER) #bytes(int(str_byte,0))
                #print(f"Addr: {my_addr} Data: {mem_struct[my_addr]}")
                my_addr += 1
                #int() with base 10: '0xff'
            
        return mem_struct
                

    def convert_to_rom(self,rom_start,rom_len,data):
        ''' Pass in a mem_struct, let it know the start addr and total bytes of the
            ROM. this'll return a bytearray of the ROM
        '''
        rom_start = int(rom_start,0)
        rom_len = int(rom_len,0)
        print(f"Rom Start: {rom_start} Rom End: {rom_start + rom_len}")
        
        rom_mem = bytearray()
        for idx in range(rom_len):
            data_addr = rom_start + idx
            if data_addr in data:
                my_byte = data[data_addr]
            else:
                my_byte = (0x00).to_bytes(1, byteorder=BYTEORDER)
            #print(f"Addr: {idx} Data: {my_byte}")
            rom_mem += my_byte
        return rom_mem


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')
    parser.add_argument('infile', help='the ASM filename for input')
    parser.add_argument('outfile', help='the output ROM name')
    parser.add_argument('-s', '--rom_start', help='The start address of the ROM when installed in the host')
    parser.add_argument('-l', '--rom_length', help='The total addresses on the rom')
    parser.add_argument('-v', '--verbose',
                        action='store_true')

    args = parser.parse_args()

    gr8a = Gr8Assembler()

    lines, line_ids = gr8a.recursive_file_read(args.infile)
    lineinfo,lineaddr,lines = gr8a.parse_lines(lines,line_ids)

    mem_struct = gr8a.make_mem_struct(lineaddr,lines)
    
    my_rom = gr8a.convert_to_rom(args.rom_start,args.rom_length,mem_struct)
        
    print("ROM CONTENTS:")
    print(hexdump(my_rom))
    # this is from 'helpers'
    write_rom(args.outfile,my_rom)
    
    # %Run assembler.py sp_test.asm 16k_rom.hex -s 0xc000 -l 16384
