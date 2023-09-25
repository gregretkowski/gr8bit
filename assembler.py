#

'''
TODO:
Set to turbo syntax
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
        lineinfo, lineadr, labels = [], [], {}
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
                labels[lines[i][:lines[i].find(':')]] = i   # put label with it's line number into dictionary
                lines[i] = lines[i][lines[i].find(':')+1:]  # cut out the label

            lines[i] = lines[i].split()                     # now split line into list of bytes (omitting whitepaces)

            for j in range(len(lines[i])-1, -1, -1):        # iterate from back to front while inserting stuff
                #if "0x0302" == lines[i][j]:
                #    print(lines[i][j])
                #    raise("found the val!")
                try: lines[i][j] = str(opCodes[lines[i][j]][0])     # try replacing mnemonic with opcode
                except: 
                    if lines[i][j].find('0x') == 0 and len(lines[i][j]) > 4:    # replace '0xWORD' with 'LSB MSB'
                        val = int(lines[i][j], 16)
                        lines[i][j] = str(val & 0xff)
                        if not eight_bit_addresses:
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
                    labels[e]; lines[i].insert(j+1, '0x@@') # is this element a label? => add a placeholder for the MSB
                except: pass
            if lineinfo[i] & LINEINFO_ORG: adr = lineinfo[i] & 0xffff   # react to #org by resetting the address
            lineadr.append(adr);                            # save line start address
            adr += len(lines[i])                            # advance address by number of (byte) elements

        for l in labels: labels[l] = lineadr[labels[l]]     # update label dictionary from 'line number' to 'address'

        for i in range(len(lines)):                         # PASS 3: replace 'reference + placeholder' with 'MSB LSB'
            for j in range(len(lines[i])):
                e = lines[i][j]; pre = ''; off = 0
                if isinstance(e, str):
                    if e[0] == '<' or e[0] == '>': pre = e[0]; e = e[1:]
                    if e.find('+') != -1: off += int(e[e.find('+')+1:], 0); e = e[0:e.find('+')]
                    if e.find('-') != -1: off -= int(e[e.find('-')+1:], 0); e = e[0:e.find('-')]
                try:
                    adr = labels[e] + off
                    if pre == '<': lines[i][j] = str(adr & 0xff)
                    elif pre == '>': lines[i][j] = str((adr>>8) & 0xff)
                    else:
                        lines[i][j] = str(adr & 0xff)
                        #if eight_bit_addresses:
                        #    del lines[i][j+1]
                        #    j+=1
                        #else:
                        lines[i][j+1] = str((adr>>8) & 0xff)
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
                    #print(e)
                    insert += ('%02.2x' % (int(e, 0) & 0xff)) + ' '
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
