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
from functools import cached_property
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
            if len(address) == 3:
                offset = address[2]
            else:
                offset = 0
            return ((address[0] << 8) | address[1]) + offset
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
            'SR': Register(), # FLAGS register
            'SD': Register() # STATUS DISPLAY register
        }
        
        self.opcodes = {x[1][0]: x[0]  for x in opCodes.items()}
        
        self.hlt = False
        
    
        self.reg['PCH'].set(0xff)
        self.reg['PCL'].set(0xfc)
        self.reg['SR'].set(0x00)
        self.reg['SD'].set(0x00)
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
        
        def sd_update(value):
            self.log.debug("STATUS DISPLAY: %s" % hex(value).upper())
            self.reg['SD'].set(value)
            

        write_callbacks={
            0x8000: sd_update
        }
        self.memory = Memory((64 * 1024),write_callbacks=write_callbacks) # 64k of memory
 
    def system_status(self):
        pc = self.reg['PCH'].get() << 8 | self.reg['PCL'].get()
        self.sd_win.addstr(0,2,f"                                             ") # Cheap clear
        self.sd_win.addstr(0,2,f" SD:{self.reg['SD'].get():#0{4}x} PC:{pc:#0{6}x} A:{self.reg['A'].get():#0{4}x} X:{self.reg['X'].get():#0{4}x} SP:{self.reg['SP'].get():#0{4}x} ", curses.A_REVERSE)                         
        #self.sd_win.addstr(0,2,f" Status Display: {value:#0{4}x} ", curses.A_REVERSE) # % hex(value).upper() )
        self.sd_win.refresh()
   
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
        self.cons_win.addstr(2,2,"TODO Implement UART I/O")
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
  
    def _stack_push(self, value):
        # write, increment
        self.memory.write([0x01, self.reg['SP'].get()], value)
        self.reg['SP'].inc()
        if self.reg['SP'].get() > 255:
            raise Exception("Stack overflow")

    def _stack_pop(self):
        # decrement, read
        self.reg['SP'].dec()
        if self.reg['SP'].get() < 0:
            raise Exception("Stack underflow")
        return self.memory.read([0x01, self.reg['SP'].get()])

    def _get_flag(self, flag):
        return ((self.reg['SR'].get() >> self.FLAGS[flag]) & 1)
 
    def _set_flag(self, flag, value):
        if value == 0:
            self.reg['SR'].set(self.reg['SR'].get() & ~(1 << self.FLAGS[flag]))
        elif value == 1:
            self.reg['SR'].set(self.reg['SR'].get() | (1 << self.FLAGS[flag]))
            pass
        else:
            raise Exception("cant set flag only zero or one")
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

    def run(self,tick=0.0):
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
                if self.reg['A'].get() < val:
                    self.log.debug("CMP: A:%s < I:%s" % (self.reg['A'].get(),val))
                    self._set_flag('zero',0)
                    self._set_flag('carry',0)
                elif self.reg['A'].get() == val:
                    self.log.debug("CMP: A:%s == I:%s" % (self.reg['A'].get(),val))
                    self._set_flag('negative',0)
                    self._set_flag('zero',1)
                    self._set_flag('carry',1)
                elif self.reg['A'].get() > val:
                    self.log.debug("CMP: A:%s > I:%s" % (self.reg['A'].get(),val))
                    self._set_flag('zero',0)
                    self._set_flag('carry',1)
                else:
                    raise(Exception("CMP failed"))
                self.log.debug(f"SR: {bin(self.reg['SR'].get())}") # % bin(self.reg['SR'].get()))")
            elif opcode == 'BEQ':
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                if self._get_flag('zero') == 1:
                    self.reg['PCL'].set(pcl)
                    self.reg['PCH'].set(pch)
                    self.log.debug("BEQ Taking Branch")
                else:
                    self.log.debug("BEQ Skipping Branch")

            elif opcode == 'HLT':
                self.log.info("HLT encountered")
                self.hlt = True
            elif opcode == 'JSR':
                # pc low, pc high, 
                self._stack_push(self.reg['PCL'].get())
                self._stack_push(self.reg['PCH'].get())
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                self.reg['PCL'].set(pcl)
                self.reg['PCH'].set(pch)

            elif opcode == 'RTS':
                pch = self._stack_pop()
                pcl = self._stack_pop()
                self.reg['PCL'].set(pcl)
                self.reg['PCH'].set(pch)
                self.inc_pc()
                self.inc_pc()
            elif opcode == 'PHA':
                self._stack_push(self.reg['A'].get())
            elif opcode == 'PLA':
                self.reg['A'].set(self._stack_pop())
                
            elif opcode == 'TAX':
                self.reg['X'].set(self.reg['A'].get())
            elif opcode == 'TXA':
                self.reg['A'].set(self.reg['X'].get())
            elif opcode == 'DEX':
                self.reg['X'].dec()
            elif opcode == 'INX':
                self.reg['X'].inc()
            # test memory access pointer and x index (via x index?)
            elif opcode == 'LPX':
                # get low/high addr pointer,
                # set the mem addr to the address of that pointer
                # and then load A from the data, indexed by X
                # LPX 0xPPPP - Load Acc with value from INDIRECT (pointer) address, indexed by X register.
                # ex. 'LPX 0x0080' - if $80 = 00 and $81 = 10, and X = $05 - would get contents from $1000+5

                # NOT IMPLEMENTED RIGHT _ GET /POINTER!/ and read that memory location
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low])
                addr_high = self.memory.read([ptr_high, ptr_low+1])
                self.log.debug("LPX addr_low: %s addr_high %s X %s" % (hex(addr_low),hex(addr_high),self.reg['X'].get()))
                self.reg['A'].set(self.memory.read([addr_high, addr_low, self.reg['X'].get()]))

            elif opcode == 'SPX':
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low])
                addr_high = self.memory.read([ptr_high, ptr_low+1])
                #addr_low = self._read_and_inc()
                #addr_high = self._read_and_inc()
                self.log.debug("SPX addr_low: %s addr_high %s X %s" % (hex(addr_low),hex(addr_high),self.reg['X'].get()))
                self.memory.write([addr_high, addr_low, self.reg['X'].get()], self.reg['A'].get())
                #self.reg['A'].get(self.memory.read([addr_high, addr_low, self.reg['X'].get()]))
            elif opcode == 'BCS':
                # Branch if carry set
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                if self._get_flag('carry') == 1:
                    self.reg['PCL'].set(pcl)
                    self.reg['PCH'].set(pch)
                    self.log.debug("BCS Taking Branch")
                else:
                    self.log.debug("BCS Skipping Branch")
            elif opcode == 'TFA':
                # trasnsfer from  status register to accumulator
                self.reg['A'].set(self.reg['SR'].get())
            elif opcode == 'TAF':
                # trasnsfer from  accumulator to status register
                self.reg['SR'].set(self.reg['A'].get())
            elif opcode == 'CLF':
                # Clear flags register
                self.reg['SR'].set(0x00)
                
            elif opcode == 'ADD':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                value = self.memory.read([addr_high, addr_low])
                res = self.reg['A'].get() + value + self._get_flag('carry')
                if res > 255:
                    self._set_flag('carry',1)
                    res = res - 256
                self.reg['A'].set(res)
            elif opcode == 'AND':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                value = self.memory.read([addr_high, addr_low])
                self.reg['A'].set(self.reg['A'].get() & value)
                # Logic ops set negative and zero flag
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'ORA':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                value = self.memory.read([addr_high, addr_low])
                self.reg['A'].set(self.reg['A'].get() | value)
                # Logic ops set negative and zero flag
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'XOR':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                value = self.memory.read([addr_high, addr_low])
                self.reg['A'].set(self.reg['A'].get() ^ value)
                # Logic ops set negative and zero flag
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'ASL':
                # shift left
                #self.reg['A'].set(self.reg['A'].get() << 1)
                carry_bit = self._get_flag('carry')
                self.reg['A'].set((self.reg['A'].get() << 1) + carry_bit)
                # Shifts set negative, zero and carry flags
                if self.reg['A'].get() > 255:
                    self._set_flag('carry',1)
                    self.reg['A'].set(self.reg['A'].get() - 256)
                # Shifts set negative, zero and carry flags
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'ASR':
                # shift right
                #self.reg['A'].set(self.reg['A'].get() << 1)
                # Shifts set negative, zero and carry flags
                self.log.debug(f"A:{self.reg['A'].get()}")
                carry_bit = self._get_flag('carry')
                if self.reg['A'].get() > 127:
                    self._set_flag('carry',1)
                    
                self.reg['A'].set(((self.reg['A'].get() >> 1) + (128 * carry_bit)) )
                self.log.debug(f"A:{self.reg['A'].get()}")

                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'LDX':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                self.reg['X'].set(self.memory.read([addr_high, addr_low]))
            elif opcode == 'STX':
                addr_low = self._read_and_inc()
                addr_high = self._read_and_inc()
                self.memory.write([addr_high, addr_low], self.reg['X'].get())
            elif opcode == 'JPX':
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low, self.reg['X'].get() ])
                addr_high = self.memory.read([ptr_high, ptr_low+1, self.reg['X'].get()])
                # Get Addresses
                self.reg['PCL'].set(addr_low)
                self.reg['PCH'].set(addr_high)
            elif opcode == 'LAX':
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low, self.reg['X'].get() ])
                addr_high = self.memory.read([ptr_high, ptr_low+1, self.reg['X'].get()])
                self.reg['A'].set(self.memory.read([addr_high, addr_low, self.reg['X'].get()]))
            elif opcode == 'SAX':
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low, self.reg['X'].get() ])
                addr_high = self.memory.read([ptr_high, ptr_low+1, self.reg['X'].get()])
                self.memory.write([addr_high, addr_low, self.reg['X'].get()], self.reg['A'].get())
                
            else:
                self.log.error("Un-implemented opcode %s" % opcode)
                while True:
                    time.sleep(0.1)
                #raise(Exception("Unknown opcode %s" % opcode))
            self.system_status()
            time.sleep(tick)
        self.log.info("HLT encountered, halted!")
        while True:
            time.sleep(0.1)
#self.registers['PCL'].set(0xfffc)

    
if __name__ == "__main__":
    # parse arguments using argparse module
    parser = argparse.ArgumentParser(description='Emulate a CPU')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    #arser.add_argument('--pausesion='store_true', help='Enable debug mode')
    # add an argument to have a tick time
    parser.add_argument('--tick', type=float, help='Clock tick time - adds delay for each tick')

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
        cpu.run(args.tick)
    curses.wrapper(go)
    



  

    pass
