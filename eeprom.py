import os
import sys
import struct
import time
import argparse
from smbus import SMBus

from eeprom_chip import EEPROMChip

class EEPROM:
    BUS = 0
    SLAVE_ADDRESS = 0x56
    DUMP_SIZE = 256
    CLEAN_SIZE = 256
    CHUNK_SIZE = 8              # fru data length is always in multiples of 8 bytes
    WRITE_DELAY_SEC = 0.015     # data sheet says 5 ms max
    BIN_FILENAME = "eeprom.bin"
    CHIP_NAME = "24C128"
    
    def __init__(self, chip_name=CHIP_NAME, bus=BUS, slave_addr=SLAVE_ADDRESS):
        self.chip_info = EEPROMChip(chip_name)
        self.bus = bus
        self.slave_addr = slave_addr
        self.dump_size = self.DUMP_SIZE
        self.clean_size = self.CLEAN_SIZE
        self.bin_filename = self.BIN_FILENAME
        self.delay_sec = self.WRITE_DELAY_SEC
        self.smb = SMBus(self.bus)

    def __del__(self):
        self.smb.close()

    def set_addr(self, offset):
        '''
        For eeprom offset length > 8bits , need to send MSB & LSB 

        '''
        return(self.smb.write_byte_data(self.slave_addr, (offset >> 8) & 0xff, offset & 0xff))

    def read_byte(self, offset):
        if (offset >= self.chip_info.get_eeprom_bytes()):
            print("Read EEPROM offset ({0}) can't >= EEPROM size ({1} bytes)"\
                .format(hex(offset), self.chip_info.get_eeprom_bytes()))
            return sys.exit(1)
            
        if self.chip_info.get_eeprom_offset_length() == 1:
            return(self.smb.read_byte_data(self.slave_addr, offset))
        else:
            self.set_addr(offset)
            return self.smb.read_byte(self.slave_addr)

    def read_block(self, offset, length):
        if (offset % self.chip_info.get_eeprom_page_size() + length) > self.chip_info.get_eeprom_page_size():
            print("Read EEPROM page size ({0} bytes) overflow !".format(
                self.chip_info.get_eeprom_page_size()))
            return sys.exit(1)

        else:
            if self.chip_info.get_eeprom_offset_length() == 1:
                return(self.smb.read_i2c_block_data(self.slave_addr, offset, length))

            else:
                self.set_addr(offset)
                return [self.smb.read_byte(self.slave_addr) for index in range(length)]

    def write_byte(self, offset, byte_data):
        if (offset >= self.chip_info.get_eeprom_bytes()):
            print("Write EEPROM offset ({0}) can't >= EEPROM size ({1} bytes)"\
                .format(hex(offset), self.chip_info.get_eeprom_bytes()))
            return sys.exit(1)
        
        if self.chip_info.get_eeprom_offset_length() == 1:
            self.smb.write_byte_data(self.slave_addr, offset, byte_data)
            time.sleep(self.delay_sec)
        else:
            self.smb.write_i2c_block_data(self.slave_addr, (offset >> 8) & 0xff, 
                                          [offset & 0xff, byte_data])
            time.sleep(self.delay_sec)

    def write_block(self, offset, data):
        if (offset % self.chip_info.get_eeprom_page_size() + len(data)) > self.chip_info.get_eeprom_page_size():
            print("Write EEPROM page size ({0} bytes) overflow !".format(
                self.chip_info.get_eeprom_page_size()))
            return sys.exit(1)
        else:
            if self.chip_info.get_eeprom_offset_length() == 1:
                self.smb.write_i2c_block_data(self.slave_addr, offset, data)
                time.sleep(self.delay_sec)
            else:
                data.insert(0, offset & 0xff)
                self.smb.write_i2c_block_data(self.slave_addr, (offset >> 8) & 0xff, data)
                time.sleep(self.delay_sec)
                self.set_addr(0)

    def set_dump_size(self, size):
        if (size > self.chip_info.get_eeprom_bytes()):
            print("Set EEPROM dump size ({0} bytes) can't larger than EEPROM size ({1} bytes)\n"\
                .format(size, self.chip_info.get_eeprom_bytes()))
            return sys.exit(1)
        self.dump_size = size
    
    def decode_data(self, byte):
        return chr(byte) if byte >= 0x30 and byte <= 0x7F else "."

    def dump_to_console(self):
        # print the byte title
        sys.stdout.write('      ')
        for i in range(0, 16):
            sys.stdout.write(''.join(format(i, '01x')))
            sys.stdout.write('  ')
        
        sys.stdout.write('  ')
        [sys.stdout.write(''.join(format(i, '01x'))) for i in range(16)]  
        sys.stdout.write('\n')

        # print the raw title
        data_list=[]
        offset = 0
        sys.stdout.write(''.join(format(offset, '04x')))
        sys.stdout.write(': ')
        while offset < self.dump_size:
            data = self.read_byte(offset)
            data_list.append(data)
            sys.stdout.write(''.join(format(data, '02x')))
            sys.stdout.write(' ')
            offset += 1
                     
            if offset % 16 == 0 :    
                sys.stdout.write('  ')
                sys.stdout.write(''.join(self.decode_data(i) for i in data_list))  
                if offset < self.dump_size:
                    sys.stdout.write('\n')
                    sys.stdout.write(''.join(format(offset, '04x')))
                    sys.stdout.write(': ')
                data_list=[]
        print("")

    def set_bin_filename(self, filename):
        self.bin_filename = filename
    
    def set_clean_size(self, size):
        if (size > self.chip_info.get_eeprom_bytes()):
            print("Set EEPROM clean size ({0} bytes) can't larger than EEPROM size ({1} bytes)\n"\
                .format(size, self.chip_info.get_eeprom_bytes()))
            return sys.exit(1)
        self.clean_size = size
    
    def clean(self):
        '''
         smbus tool support R/W block max length:32 , write 16 bytes each time is safe
         
        '''
        block = 16 if self.chip_info.get_eeprom_page_size() >= 16 else self.chip_info.get_eeprom_page_size() 
        for offset in range(0, self.clean_size, block):
            data = [0xff] * block
            self.write_block(offset, data)

    def dump_to_file(self):
        offset = 0
        with open(self.bin_filename, "wb") as f:
            while offset < self.dump_size:
                data = self.read_byte(offset)
                f.write(struct.pack('1B', data))
                offset += 1

    def bytes_from_file(self):
        with open(self.bin_filename, "rb") as f:
            while True:
                chunk = f.read(self.CHUNK_SIZE)
                if chunk:
                    yield chunk
                else:
                    break

    def write_bin_to_eeprom(self):
        offset = 0
        for data in self.bytes_from_file():
            byte_list = list(bytearray(data))
            self.write_block(offset, byte_list)
            offset += self.CHUNK_SIZE


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='EEPROM utility for FRU'
    )

    def auto_int(x):
        return int(x, 0)
    
    parser.add_argument('bus',
                        type=int,
                        default=0,
                        nargs='?',
                        help='EEPROM BUS, default bus 0')

    parser.add_argument('address',
                        type=auto_int,
                        default=0x51,
                        nargs='?',
                        help='EEPROM address, default address 0x51')
    
    parser.add_argument('chip',
                        type=str,
                        nargs='?',
                        default= "24C128",
                        help='EEPROM chip type, default chip type 24C128')
    
    parser.add_argument('-edc', '--eeprom-dump-console',
                        action='store_true',
                        help='Dump EEPROM to console, default dump size 256 bytes')

    parser.add_argument('-edf', '--eeprom-dump-file',
                        type=str,
                        help='Dump EEPROM to file, default dump size 256 bytes')

    parser.add_argument('-eds', '--eeprom-dump-size',
                        type=int,
                        help='EEPROM dump size, the size should be {}-times bytes'.format(EEPROM.CHUNK_SIZE))

    parser.add_argument('-ec', '--eeprom-clean',
                        action='store_true',
                        help='EEPROM clean')

    parser.add_argument('-ecs', '--eeprom-clean-size',
                        type=int,
                        help='EEPROM clean size, the size should be {}-times bytes'.format(EEPROM.CHUNK_SIZE))

    parser.add_argument('-ewb', '--eeprom-write-bin',
                        type=str,
                        help='Write bin file to EEPROM')
    
    parser.add_argument('-r', '--read',
                        action='store_true',
                        help='Read EEPROM offset value')
    
    parser.add_argument('-rb', '--read-block',
                        action='store_true',
                        help='Read EEPROM offset block value')
    
    parser.add_argument('-rbs', '--read-block-size',
                        type=int,
                        help='Specify block value to read')
        
    parser.add_argument('-w', '--write',
                        action='store_true',
                        help='Write value to EEPROM offset')
    
    parser.add_argument('-wb', '--write-block',
                        action='store_true',
                        help='Write block value to EEPROM offset')
      
    parser.add_argument('-o', '--offset',
                        type=auto_int,
                        help='Specify EEPROM offset')
    
    parser.add_argument('-d', '--data',
                        type=auto_int,
                        help='Write data to EEPROM offset')
    
    parser.add_argument('-dl', '--data-list',
                        nargs='+',
                        help='Write data list to EEPROM offset')
        
    args = parser.parse_args()
    print("EEPROM chip:"+ args.chip + " EEPROM bus:" + str(args.bus) + " address:0x" + ''.join(format(args.address, '02x')))

    def size_error():
        print("The size is not {}-times".format(EEPROM.CHUNK_SIZE))
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.eeprom_dump_size:
        if args.eeprom_dump_size % EEPROM.CHUNK_SIZE != 0:
            size_error()

    if args.eeprom_clean_size:
        if args.eeprom_clean_size % EEPROM.CHUNK_SIZE != 0:
            size_error()

    if args.eeprom_dump_file and args.eeprom_write_bin:
        print("Dump bin and write bin can't work at the same time")
        parser.print_help(sys.stderr)
        sys.exit(1)

    eeprom = EEPROM(args.chip, args.bus, args.address)
    if args.eeprom_dump_console:
        if args.eeprom_dump_size:
            eeprom.set_dump_size(args.eeprom_dump_size)
        eeprom.dump_to_console()

    if args.eeprom_dump_file:
        basename, ext = os.path.splitext(os.path.basename(args.eeprom_dump_file))
        if ext != '.bin':
            print('Refusing to dump to file not ending with .bin')
            sys.exit(1)
        if args.eeprom_dump_size:
            eeprom.set_dump_size(args.eeprom_dump_size)
        eeprom.set_bin_filename(args.eeprom_dump_file)
        eeprom.dump_to_file()
        print("Save EEPROM contents to {0} done !".format(args.eeprom_dump_file))
        
    if args.eeprom_clean:
        if args.eeprom_clean_size:
            eeprom.set_clean_size(args.eeprom_clean_size)
        eeprom.clean()
        print("Clear EEPROM {0} bytes done !".format(eeprom.clean_size))

    if args.eeprom_write_bin:
        basename, ext = os.path.splitext(os.path.basename(args.eeprom_write_bin))
        if ext != '.bin':
            print('Refusing to read a bin file not ending with .bin')
            sys.exit(1)
        eeprom.set_bin_filename(args.eeprom_write_bin)
        eeprom.write_bin_to_eeprom()
        print("Write {0} to eeprom done !".format(args.eeprom_write_bin))
        
    if args.read:
        if args.offset != "":
            print("Offset:{0} value:{1}".format(hex(args.offset), hex(eeprom.read_byte(args.offset))))
        else:
            print("Read byte needs to type offset\n")
    
    if args.read_block:
        if args.offset != "" and args.read_block_size != "":
            print("Offset:{0} block size:{1} \nblock value:{2}".format(hex(args.offset), \
                args.read_block_size, [hex(x) for x in eeprom.read_block(args.offset, args.read_block_size)]))
        else:
            print("Read block data needs to type offset and block size\n")
            
    if args.write: 
        if args.offset != "" and args.data != "":
            print("Write:{0} to offset:{1} ".format(hex(args.data), hex(args.offset)))
            eeprom.write_byte(args.offset, args.data)
        else:
            print("Write data needs to type offset and data\n") 
    
    if args.write_block: 
        if args.offset != "" and args.data_list != "":
            print("From offset:{0} to write block data :{1} ".format(hex(args.offset), args.data_list))
            eeprom.write_block(args.offset, list(map(auto_int, args.data_list)))
        else:
            print("Write block data needs to type offset and data list\n") 
    

