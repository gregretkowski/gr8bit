# an emulator for a cpu

'''
Python emulator for the GR8 CPU
'''

import argparse
# pip install windows-curses
import curses
from functools import cached_property
from genericpath import samefile
import logging
import tempfile
import time

# the opcodes used for this cpu
from opcodes import opCodes
from assembler import Gr8Assembler


class CursesHandler(logging.Handler):
    MAX_LINES = 10
    def __init__(self, screen):
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

            screen.clear()
            for x,msg in enumerate(self.linebuffer):
                screen.addstr(x+1,2,msg)
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
    # Storing memory as ints
    def __init__(self, memory_size, read_callbacks={}, write_callbacks={}):
        # Initialize memory with zeros
        self.memory = [0] * memory_size
        # callbacks contain a list of mem addrs and the function to call when that addr is read/written
        self.read_callbacks = read_callbacks
        self.write_callbacks = write_callbacks

    def _get_addr(self, address):
        if isinstance(address, list):
            # Three args means indexed memory op.
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
        if address in self.read_callbacks:
            return self.read_callbacks[address]()
        elif 0 <= address < len(self.memory):
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
        self.terminal_buffer = ['']
        self.key_ready = 0x00
        self.keybuffer = 0x00

        self.reg['PCH'].set(0xff)
        self.reg['PCL'].set(0xfc)
        self.reg['SR'].set(0x00)
        self.reg['SD'].set(0x00)
        self._curses_setup()
        
        # Logging setup for curses
        self.log = logging.getLogger(__name__)
        self.log.propagate = False
        self.log.setLevel(log_level)
        mh = CursesHandler(self.log_win)
        mf = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%H:%M:%S')
        mh.setFormatter(mf)
        self.log.addHandler(mh)
        
        # Memory-Mapped IO emulation
        def sd_update(value):
            self.log.debug("STATUS DISPLAY: %s" % hex(value).upper())
            self.reg['SD'].set(value)
        
        def term_write(value):
            self.terminal_write(value)

        write_callbacks={
            0x8000: sd_update,
            0x8001: term_write,
        }

        def read_keyready():
             self.log.debug("read_keyready %s" % self.key_ready)
             return self.key_ready
        
        def read_keyread():
            self.log.debug("read_keybuffer %s" % self.keybuffer)
            mykey = self.keybuffer
            self.key_ready = 0
            self.keybuffer = 0
            return mykey
        
        read_callbacks={
            0x8003: read_keyready,
            0x8002: read_keyread,
        }

        self.memory = Memory((64 * 1024),write_callbacks=write_callbacks, read_callbacks=read_callbacks) # 64k of memory
        # Init Done! 

    def terminal_write(self,value_int):
        try:
            value = chr(value_int)
            if value_int == 0:
                return
            if value == '\n':
                self.terminal_buffer.append('')
            else:
                self.terminal_buffer[-1] += value
                
            rows, cols = self.cons_win.getmaxyx()
            if len(self.terminal_buffer) > rows-2:
                self.terminal_buffer.pop(0)

            self.cons_win.clear()
            for x,msg in enumerate(self.terminal_buffer):
                self.cons_win.addstr(x+1,2,msg)
            
            self.cons_win.box()
            self.cons_win.refresh()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            raise
    

    def system_status(self):
        pc = self.reg['PCH'].get() << 8 | self.reg['PCL'].get()
        self.sd_win.addstr(0,2,f"                                             ") # Cheap clear
        self.sd_win.addstr(0,2,f" SD:{self.reg['SD'].get():#0{4}x} PC:{pc:#0{6}x} A:{self.reg['A'].get():#0{4}x} X:{self.reg['X'].get():#0{4}x} SP:{self.reg['SP'].get():#0{4}x} ", curses.A_REVERSE)                         
        self.sd_win.refresh()
   
    def _curses_setup(self):
        height, width = self.screen.getmaxyx()
        cols_mid = int(0.5*width)
        self.cons_win = self.screen.subwin(1, 0)
        self.log_win = self.screen.subwin(height-2, cols_mid, 1, cols_mid)
        self.sd_win = self.screen.subwin(0, 0)
        self.cons_win.box()
        self.log_win.box()
        self.cons_win.addstr(2,2,"TODO Implement UART I/O")
        self.sd_win.addstr(0,2,"Status Disaplay %s" % "0x00" )
        self.log_win.addstr(2,2,"Logging window")
        self.log_win.scrollok(True)
        self.log_win.idlok(True)
        self.screen.nodelay(True)
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
        # TODO/BUG: When the A register is set, the negative and zero flags are not set
        if value == 0:
            self.reg['SR'].set(self.reg['SR'].get() & ~(1 << self.FLAGS[flag]))
        elif value == 1:
            self.reg['SR'].set(self.reg['SR'].get() | (1 << self.FLAGS[flag]))
            pass
        else:
            raise Exception("cant set flag only zero or one")

    def build(self, filename, rom_start="0xc000", rom_length="16384"):
        # Assembles the file and loads it into memory - analog to:
        #     assembler.py smoketest.asm 16k_rom.hex -s 0xc000 -l 16384

        gr8a = Gr8Assembler(logger=self.log)
        
        lines, line_ids = gr8a.recursive_file_read(filename)
        lineinfo,lineaddr,lines = gr8a.parse_lines(lines,line_ids)

        mem_struct = gr8a.make_mem_struct(lineaddr,lines)
    
        for k,v in mem_struct.items():
            self.memory.write(k,int.from_bytes(v))
        self.log.debug("loaded %s items into memory",len(mem_struct))
        self.log.debug("item at fffc: %s" % self.memory.read(0xfffc))

    def _read_and_inc(self):
        val = self.memory.read(self.pc())
        self.inc_pc()
        return val

    def run(self,tick=0.0):
        self.log.debug("in run()")
        # start at boot location fffc
        while not self.hlt:

            opcode_int = self._read_and_inc()
            opcode = (self.opcodes[opcode_int])
            self.log.debug("Processing Opcode %s" % opcode)
        
            if opcode == 'JMP':
                pcl = self._read_and_inc()
                pch = self._read_and_inc()
                self.reg['PCL'].set(pcl)
                self.reg['PCH'].set(pch)
            elif opcode == 'LDI':
                self.reg['A'].set(self._read_and_inc())
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
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
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
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
                self.log.debug(f"SR: {bin(self.reg['SR'].get())}")
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
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
                
            elif opcode == 'TAX':
                self.reg['X'].set(self.reg['A'].get())
                self._set_flag('negative',self.reg['X'].get() >> 7)
                self._set_flag('zero',self.reg['X'].get() == 0)
            elif opcode == 'TXA':
                self.reg['A'].set(self.reg['X'].get())
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
            elif opcode == 'DEX':
                self.reg['X'].dec()
                self._set_flag('negative',self.reg['X'].get() >> 7)
                self._set_flag('zero',self.reg['X'].get() == 0)
            elif opcode == 'INX':
                self.reg['X'].inc()
                self._set_flag('negative',self.reg['X'].get() >> 7)
                self._set_flag('zero',self.reg['X'].get() == 0)
            # test memory access pointer and x index (via x index?)
            elif opcode == 'LPX':
                # get low/high addr pointer,
                # set the mem addr to the address of that pointer
                # and then load A from the data, indexed by X
                # LPX 0xPPPP - Load Acc with value from INDIRECT (pointer) address, indexed by X register.
                # ex. 'LPX 0x0080' - if $80 = 00 and $81 = 10, and X = $05 - would get contents from $1000+5
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low])
                addr_high = self.memory.read([ptr_high, ptr_low+1])
                self.log.debug("LPX addr_low: %s addr_high %s X %s" % (hex(addr_low),hex(addr_high),self.reg['X'].get()))
                self.reg['A'].set(self.memory.read([addr_high, addr_low, self.reg['X'].get()]))
                self._set_flag('zero',self.reg['A'].get() == 0)

            elif opcode == 'SPX':
                ptr_low = self._read_and_inc()
                ptr_high = self._read_and_inc()
                addr_low = self.memory.read([ptr_high, ptr_low])
                addr_high = self.memory.read([ptr_high, ptr_low+1])
                self.log.debug("SPX addr_low: %s addr_high %s X %s" % (hex(addr_low),hex(addr_high),self.reg['X'].get()))
                self.memory.write([addr_high, addr_low, self.reg['X'].get()], self.reg['A'].get())
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
            
            # TODO: Ensure all math ops set flags properly
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
                carry_bit = self._get_flag('carry')
                self.reg['A'].set((self.reg['A'].get() << 1) + carry_bit)
                # Shifts set negative, zero and carry flags
                if self.reg['A'].get() > 255:
                    self._set_flag('carry',1)
                    self.reg['A'].set(self.reg['A'].get() - 256)
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
                self._set_flag('negative',self.reg['X'].get() >> 7)
                self._set_flag('zero',self.reg['X'].get() == 0)
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
                self._set_flag('negative',self.reg['A'].get() >> 7)
                self._set_flag('zero',self.reg['A'].get() == 0)
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
            self.system_status()
            # Check for input...
            my_char = self.screen.getch()
            if my_char != -1:
                self.log.debug("Got char %s" % my_char)
                self.keybuffer = my_char
                self.key_ready = 1

            time.sleep(tick)
        self.log.info("HLT encountered, halted!")
        while True:
            time.sleep(0.1)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Emulate a CPU')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--tick', type=float, default=0.0, help='Clock tick time - adds delay for each tick')
    parser.add_argument('filename', type=str, help='File to load into memory')
    args = parser.parse_args()
    
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logger.INFO
    
    def go(screen):
        cpu = CPU(screen=screen,log_level=log_level)
        cpu.build(args.filename)
        cpu.run(args.tick)
    curses.wrapper(go)
    