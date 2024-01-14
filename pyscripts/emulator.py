# an emulator for a cpu

'''
Emulate my CPU.. Steps:

Take a assembly file and convert it to binary..
Load the binary into memory..
Run the program..

implemnt a memory
start at boot location fffc
implement each opcode

implement 'uart' for input/output




'''

import argparse
# pip install windows-curses
import curses
import logging
from os import scandir
import re
import tempfile
import time
from tkinter import SEL
from token import OP

# the opcodes used for this cpu
from opcodes import opCodes
from assembler import Gr8Assembler

#print(opCodes)

class CursesHandler(logging.Handler):
    MAX_LINES = 10
    def __init__(self, screen):
        #MAX_LINES = 3
        logging.Handler.__init__(self)
        self.screen = screen
        self.linebuffer = []
    def emit(self, record):
        try:
            msg = self.format(record)
            screen = self.screen
            rows, cols = screen.getmaxyx()
            self.linebuffer.append(msg[0:cols-2])
            if len(self.linebuffer) > rows-2:
                self.linebuffer.pop(0)

            
            #fs = "\n%s"
            #screen.addstr(fs % msg)
            #x, y = screen.getyx()
            screen.clear()
            for x,msg in enumerate(self.linebuffer):
                screen.addstr(x+1,2,msg)
            
            #screen.addstr(x+1,2,msg)
            #screen.addstr(2,2,msg)
            screen.box()
            screen.refresh()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            raise

class Register():
    def __init__(self):
        self.value = 0

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    def get(self):
        return self.value
    def set(self,value):
       self.value = value
    def inc(self):
        self.value += 1
    def dec(self):
        self.value -= 1
        
class Memory():
    # TODO: should we store as bytes or as ints????
    def __init__(self, memory_size, read_callbacks={}, write_callbacks={}):
        # Initialize memory with zeros
        self.memory = [0] * memory_size
        # callbacks contain a list of mem addrs and the function to call when that addr is read/written
        self.read_callbacks = read_callbacks
        self.write_callbacks = write_callbacks

    def _get_addr(self, address):
        if isinstance(address, list):
            return (address[0] << 8) | address[1]
        else:
            return address
  
    def read(self, address):
        address = self._get_addr(address)
        # Read from memory at the specified address
        if 0 <= address < len(self.memory):
            return self.memory[address]
        else:
            raise IndexError("Memory out of bounds")

    def write(self, address, value):
        address = self._get_addr(address)
        if address in self.write_callbacks:
            self.write_callbacks[address](value)
        # Write to memory at the specified address
        elif 0 <= address < len(self.memory):
            self.memory[address] = value
        else:
            raise IndexError("Memory out of bounds")


class CPU():
    # The position of each flag in the status register
    '''
    Flags Register BIts
        Carry
        Equal/Zero (one flag)
        Overflow
        negative

        7  bit  0
        ---- ----
        NV1B DIZC
        |||| ||||
        |||| |||+- Carry
        |||| ||+-- Zero
        |||| |+--- Interrupt Disable
        |||| +---- Decimal
        |||+------ (No CPU effect; see: the B flag)
        ||+------- (No CPU effect; always pushed as 1)
        |+-------- Overflow
        +--------- Negative
    '''
    FLAGS = {
        'carry': 0,
        'zero': 1,
        'interrupt_disable': 2,
        'decimal': 3,
        'overflow': 6,
        'negative': 7,
    }
    def __init__(self,screen, log_level=logging.INFO):
        
        self.screen = screen
        self.rom = None
        self.reg = {
            'A': Register(),
            'X': Register(),
            'PCH': Register(),
            'PCL': Register(),
            'SP': Register(),
            'SR': Register() # FLAGS register
        }
        
        self.opcodes = {x[1][0]: x[0]  for x in opCodes.items()}
        
        self.hlt = False
        
    
        self.reg['PCH'].set(0xff)
        self.reg['PCL'].set(0xfc)
        self.reg['SR'].set(0x00)
        self._curses_setup()
        # Logging setup for curses.

        self.log = logging.getLogger(__name__)
        self.log.propagate = False
        self.log.setLevel(log_level)
        mh = CursesHandler(self.log_win)
        mf = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%H:%M:%S')
        mh.setFormatter(mf)
        #logger = logging.getLogger('Test Logger')
        self.log.addHandler(mh)
        
        def status_log(value):
            self.log.debug("STATUS DISPLAY: %s" % hex(value).upper())
            self.sd_win.addstr(0,2,f"Status Display: {value:#0{4}x}    ") # % hex(value).upper() )
            self.sd_win.refresh()
        write_callbacks={
            0x8000: status_log
        }
        self.memory = Memory((64 * 1024),write_callbacks=write_callbacks) # 64k of memory
 
    def _curses_setup(self):
        height, width = self.screen.getmaxyx()
        cols_mid = int(0.5*width)
        # self.cons_win = self.screen.subwin(height, cols_mid, 0, cols_mid)
        self.cons_win = self.screen.subwin(1, 0)
        self.log_win = self.screen.subwin(height-2, cols_mid, 1, cols_mid)
        self.sd_win = self.screen.subwin(0, 0) #, height-1, 0)
        #win = self.screen.subwin(0,0)
        #subwin(n_rows, n_cols, 0, 0)
        self.cons_win.box()
        self.log_win.box()
        self.cons_win.addstr(2,2,"Testing my curses app")
        self.sd_win.addstr(0,2,"Status Disaplay %s" % "0x00" )
        self.log_win.addstr(2,2,"Logging window")
        self.log_win.scrollok(True)
        self.log_win.idlok(True)
        #self.log_win = win.subwin(0,0)
        #self.cons_win.refresh()
        self.screen.refresh()
        
        
    def pc(self):
        return self.reg['PCH'].get() << 8 | self.reg['PCL'].get()
    
    def inc_pc(self):
        self.reg['PCL'].inc()
        if self.reg['PCL'].get() == 0:
            self.reg['PCH'].inc()

    def _get_flag(self, flag):
        return ((self.reg['SR'].get() >> self.FLAGS[flag]) & 1)
 
    def _set_flag(self, flag, value):
        self.reg['SR'].set(self.reg['SR'].get() | (value << self.FLAGS[flag]))
        #return (self.reg['SR'].get() >> self.FLAGS[flag]) & 1

    def build(self, filename, rom_start="0xc000", rom_length="16384"):
        #my_rom = gr8a.convert_to_rom(args.rom_start,args.rom_length,mem_struct)
        # %Run assembler.py smoketest.asm 16k_rom.hex -s 0xc000 -l 16384
        pass
        # use a tempfile to store the binary
        gr8a = Gr8Assembler(logger=self.log)
        
        lines, line_ids = gr8a.recursive_file_read(filename)
        lineinfo,lineaddr,lines = gr8a.parse_lines(lines,line_ids)

        mem_struct = gr8a.make_mem_struct(lineaddr,lines)
    
        #self.rom = gr8a.convert_to_rom(rom_start,rom_length,mem_struct)
        for k,v in mem_struct.items():
            #print(k,v)
            self.memory.write(k,int.from_bytes(v))
            #cpu_emulator.write_memory(0x1000, 42)
            #break
        self.log.debug("loaded %s items into memory",len(mem_struct))
        self.log.debug("item at fffc: %s" % self.memory.read(0xfffc))
        
    def _read_and_inc(self):
        val = self.memory.read(self.pc())
        self.inc_pc()
        return val

    def run(self):
        self.log.debug("in run()")
        #self.cons_window("XXX")
        #elf.cons_win.addstr(2,2,"Some text to console")
        # start at boot location fffc
        while not self.hlt:

            #opcode_int = int(self.memory.read(self.pc()))
            opcode_int = self._read_and_inc()
            opcode = (self.opcodes[opcode_int])
            self.log.debug("Processing Opcode %s" % opcode)
            #logging.debug(self.opcodes[opcode])
        
            if opcode == 'JMP':
                #self.inc_pc()
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                self.reg['PCL'].set(pcl)
                self.reg['PCH'].set(pch)
            elif opcode == 'LDI':
                self.reg['A'].set(self._read_and_inc())
            elif opcode == 'STA':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                self.log.debug("addr_low: %s addr_high %s" % (hex(addr_low),hex(addr_high)))
                self.memory.write([addr_high, addr_low], self.reg['A'].get())
            elif opcode == 'LDA':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                self.log.debug("addr_low: %s addr_high %s" % (hex(addr_low),hex(addr_high)))
                self.reg['A'].set(self.memory.read([addr_high, addr_low]))
            elif opcode == 'CMP':
                val = self._read_and_inc()
                '''
                Compare Instruction Results

                Compare Result	N	Z	C
                A, X, or Y < Memory	*	0	0      0b*0000000
                A, X, or Y = Memory	0	1	1      0b00000011
                A, X, or Y > Memory	*	0	1      0b*0000001
                * The N flag will be bit 7 of A, X, or Y - Memory
                '''
                if val < self.reg['A'].get():
                    self._set_flag('zero',0)
                    self._set_flag('carry',0)
                elif val == self.reg['A'].get():
                    self._set_flag('negative',0)
                    self._set_flag('zero',1)
                    self._set_flag('carry',1)
                elif val > self.reg['A'].get():
                    self._set_flag('zero',0)
                    self._set_flag('carry',1)
                else:
                    raise(Exception("CMP failed"))
            elif opcode == 'BEQ':
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                if self._get_flag('zero') == 1:
                    self.reg['PCL'].set(pcl)
                    self.reg['PCH'].set(pch)

            elif opcode == 'HLT':
                self.log.info("HLT encountered")
                self.hlt = True
            elif opcode == 'JSR':
                self.log.error("JSR not implemented")
                while True:
                    time.sleep(0.1)
                raise Exception("JSR not implemented")
            else:
                self.log.error("Un-implemented opcode %s" % opcode)
                while True:
                    time.sleep(0.1)
                #raise(Exception("Unknown opcode %s" % opcode))
        
        self.log.info("HLT encountered, exiting")
#self.registers['PCL'].set(0xfffc)

    
if __name__ == "__main__":
    # parse arguments using argparse module
    parser = argparse.ArgumentParser(description='Emulate a CPU')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    #arser.add_argument('--pausesion='store_true', help='Enable debug mode')
    parser.add_argument('filename', type=str, help='File to load into memory')
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        log_level = logging.DEBUG
    else:
        logging.basicConfig(level=logging.INFO)
        log_level = logger.INFO
    
    def go(screen):
 
        cpu = CPU(screen=screen,log_level=log_level)
        cpu.build(args.filename)
        cpu.run()
    curses.wrapper(go)
    



  

    pass
