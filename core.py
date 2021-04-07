"""
Author: Tim Hays
This class provides the core utilities for the T34, mostly involving display
but also handling the main program loop (asking for & clasifying user input).
"""

from const import *

class Core:
    def __init__(self, objfile=None):
        self.memory = [0]*65536
        self.pc = 0     # 2 bytes
        self.ac = 0     # ac, x, y, sp, sr are all 1 byte
        self.x = 0
        self.y = 0
        self.sr = 0
        self.sp = 0xFF

        self.arg1 = 0x00
        self.arg2 = 0x00
        self.amod = None

        if objfile:
            self.loadFile(objfile)

    def main(self):
        """ The main program loop """
        while True:
            try:
                instr = input('> ')
            except EOFError:
                # Catch ctrl-D
                return
            except KeyboardInterrupt:
                # Catch ctrl-C
                return

            choice = self.getInput(instr)
            cmd = choice[0]
            if cmd == 'display':
                self.display(choice[1][0], choice[1][1])
            elif cmd == 'write':
                self.write(choice[1][0], choice[1][1])
            elif cmd == 'run':
                self.run(choice[1])
            elif cmd == 'exit':
                return

    def loadFile(self, objfile):
        """ Load the file with the name given by objfile """
        for line in open(objfile):
            if line == '\n':
                continue
            bytecount = int(line[1:3], 16)
            address = int(line[3:7], 16)
            recordtype = int(line[7:9], 16)

            # End of file - drop out
            if recordtype == 1:
                return

            data = [line[i+9:i+11] for i in range(0, bytecount*2, 2)]
            data = [int(x, 16) for x in data]
            for i, item in enumerate(data):
                self.memory[address + i] = item

    def getInput(self, instr):
        """
        Based on the format of instr, returns the instruction type and information about it
        XXX - Displays the value at location XXX in memory
        XXX.YYY - Prints values from locations XXX to YYY in memory
        XXXR - Runs the program located at XXX in memory
        XXX: YY, ZZ, ... - Stores values YY, ZZ, etc starting at location XXX in memory
        """
        if '.' in instr:
            # Display range of addresses
            splitstr = instr.split('.')
            return 'display', [int(splitstr[0], 16), int(splitstr[1], 16)]

        elif instr[-1] == 'R':
            # Run a program
            return 'run', int(instr[:-1], 16)

        elif ':' in instr:
            # Write to memory
            # Get the address in base 16
            splitstr = instr.split(':')
            addr = int(splitstr[0], 16)

            # Values split by spaces
            values = splitstr[1].strip().split(' ')

            # Interpret values in base 16
            for i in range(len(values)):
                values[i] = int(values[i], 16)

            return 'write', [addr, values]

        elif instr == 'exit':
            return 'exit',

        else:
            # Display a single address
            return 'display', [int(instr, 16), int(instr, 16)]

    def display(self, start, end):
        """ Displays a range of values given by start and end"""

        # Display values from start to end
        col = 0
        for i in range(start, end+1):
            # Every 8 values, print the address at the start of the line
            if not col % 8:
                print(' ' + self.intToHex(i).ljust(6), end='')
                col = 0

            # Print this value, converted to hex
            print(self.intToHex(self.memory[i], 2) + ' ', end='')

            if i == end or not (col+1) % 8:
                print()
            col += 1

    def write(self, addr, values):
        """ Writes the given values at the given address in memory"""
        for i, val in enumerate(values):
            self.memory[addr + i] = val

    def run(self, addr):
        """ Runs the program at the address given """
        # Clear registers
        self.pc = addr
        self.ac = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFF
        self.sr = 0

        print(" PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC")

        # Main loop
        while self.sr & bitB == 0:
            cmd = self.memory[self.pc]
            func = 'self.' + CMD[cmd][0] + '()'
            self.amod = CMD[cmd][1]
            pc = self.pc
            self.getArgs(self.pc)
            exec(func)

            if 'abs' in self.amod or self.amod == 'ind':
                arg1 = self.arg1 & 0xFF
                arg2 = (self.arg1 & 0xFF00) >> 8
            else:
                arg1 = self.arg1
                arg2 = self.arg2

            print(
                self.intToHex(pc).rjust(4) +
                self.intToHex(cmd, 2).rjust(4) +
                CMD[cmd][0].rjust(5) +
                self.amod.rjust(7) +
                self.intToHex(arg1, 2).rjust(3) +
                self.intToHex(arg2, 2).rjust(3) +
                self.intToHex(self.ac, 2).rjust(4) +
                self.intToHex(self.x, 2).rjust(3) +
                self.intToHex(self.y, 2).rjust(3) +
                self.intToHex(self.sp, 2).rjust(3) +
                '{0:08b}'.format(self.sr).rjust(9)
            )
            self.pc += 1

    def getArgs(self, pc):
        """ Get arguments for an instruction and increment PC accordingly """
        if self.amod in ['impl', 'A']:
            self.arg1 = None
            self.arg2 = None
        elif self.amod in ['#', 'zpg', 'zpg,x', 'zpg,y', 'rel', 'x,ind', 'ind,y']:
            self.arg1 = self.memory[pc+1]
            self.arg2 = None
            self.pc += 1
        elif self.amod in ['abs', 'abs,x', 'abs,y', 'ind']:
            self.arg1 = self.memory[pc+1] + (self.memory[pc+2] << 8)
            self.arg2 = None
            self.pc += 2
        else:
            self.arg1 = self.memory[pc+1]
            self.arg2 = self.memory[pc+2]
            self.pc += 2


    #----- Helper Functions -----#

    def intToHex(self, n, width=0):
        """ Converts an int to a hexadecimal string with minimum width as specified """
        if n is None:
            return '--'

        ret = ''
        width = max(width, len(hex(n))-2)
        for i in range(width):
            biti = (n // int(pow(16, i))) % 16
            if biti > 9:
                biti = chr(biti + 55)
            else:
                biti = str(biti)
            ret = biti + ret

        return ret