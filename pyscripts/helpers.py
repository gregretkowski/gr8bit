class hexdump:
    def __init__(self, buf, off=0):
        self.buf = buf
        self.off = off

    def __iter__(self):
        last_bs, last_line = None, None
        for i in range(0, len(self.buf), 16):
            bs = bytearray(self.buf[i : i + 16])
            line = "{:08x}  {:23}  {:23}  |{:16}|".format(
                self.off + i,
                " ".join(("{:02x}".format(x) for x in bs[:8])),
                " ".join(("{:02x}".format(x) for x in bs[8:])),
                "".join((chr(x) if 32 <= x < 127 else "." for x in bs)),
            )
            if bs == last_bs:
                line = "*"
            if bs != last_bs or line != last_line:
                yield line
            last_bs, last_line = bs, line
        yield "{:08x}".format(self.off + len(self.buf))

    def __str__(self):
        return "\n".join(self)

    def __repr__(self):
        return "\n".join(self)


def build_rom(data, bytes_per_addr=1,mirror=True):
    # NOTE - data comes in as  a stream of bytes, but they have to be flipped
    # for whatever reason the ROM is read from file big-indian afaict!
    # ala its the human-readable format for the text file.
    
    '''
    takes a list of bytes and creates a logisim compat rom/hex file - save as *.hex

    LOGISIM HEX FILE FORMAT
    The first line identifies the file format used (currently, there is only one file format recognized). Subsequent lines list the values in little-endian hexadecimal. Logisim will assume that any values unlisted in the file are zero
    should be named *.hex ...

    v2.0 raw
    0a0f
    10e1
    2be0
    10e1
    0af7
    ...
    '''
    local_data = data.copy()
    rom_str = "v2.0 raw\n"
    i = 0
    while(i < len(data)):
        bytes_arr = []
        for byte_idx in range(bytes_per_addr):
            bytes_arr.append("{:02x}".format(local_data.pop(0)))
            #rom_str += 
            i += 1
        if mirror:
            bytes_arr.reverse()
        #    rom_str += b''.join(bytes_arr.reverse())
        #else:
        rom_str += "".join(bytes_arr)
        rom_str += "\n"
        #i += 2
    return rom_str


def write_rom(filename, data, bytes_per_addr=1,mirror=True):
    my_data = build_rom(data, bytes_per_addr, mirror)
    f = open(filename, "w")
    f.write(my_data)
    f.close()

def hex_dump(input_string, bytes_per_line=16):
    for i in range(0, len(input_string), bytes_per_line, byteorder):
        chunk = input_string[i:i + bytes_per_line]
        hex_str = ' '.join([f'{ord(c):02X}' for c in chunk])
        ascii_str = ''.join([c if 32 <= ord(c) <= 126 else '.' for c in chunk])
        print(f'{hex_str.ljust(bytes_per_line * 3)}  {ascii_str}')