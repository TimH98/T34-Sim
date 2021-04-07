"""
Author: Tim Hays
This program simulates a T34. It allows writing to memory, reading
from memory, running a program, and loading an obj file.
"""

import sys
from core import Core
from const import *


class T34(Core):
    def ADC(self):
        """ Add to accumulator with carry """
        self.sr &= (~bitN & ~bitZ & ~bitV)
        carry = 1 if (self.sr & bitC) else 0

        s1 = self.ac >= 0x80            # s1 = whether accumulator is negative
        val = self.GetValue()
        s2 = val >= 0x80
        self.ac += val + carry

        if self.ac > 0xFF:
            self.ac -= 0x100
            self.sr |= bitC
        else:
            self.sr &= ~bitC

        s3 = self.ac >= 0x80            # s3 = whether the result is negative
        if (s1 == s2) and (s1 != s3):
            self.sr |= bitV

        self.CheckNZ(self.ac)

    def AND(self):
        """ AND memory with accumulator """
        self.sr &= ~(bitN | bitZ)
        self.ac &= self.GetValue()
        self.CheckNZ(self.ac)


    def ASL(self):
        """ Arithmetic shift left """
        self.sr &= ~(bitN | bitZ | bitC)

        if self.amod == 'A':
            self.ac <<= 1
            if self.ac > 0xFF:
                self.sr |= bitC
                self.ac &= 0xFF
            self.CheckNZ(self.ac)

        else:
            val = self.GetValue()
            val <<= 1
            self.SetValue(val & 0xFF)
            if val > 0xFF:
                self.sr |= bitC
            self.CheckNZ(val)

    def BCC(self):
        """ Branch if C = 0 """
        if not (self.sr & bitC):
            self.Branch()

    def BCS(self):
        """ Branch if C = 1 """
        if self.sr & bitC:
            self.Branch()

    def BEQ(self):
        """ Branch if Z = 1 """
        if self.sr & bitZ:
            self.Branch()

    def BIT(self):
        """ Test bits """
        self.sr &= ~(bitN | bitV | bitZ)
        self.sr |= self.memory[self.arg1] & (bitN | bitV)

        if not self.arg1 & self.ac:
            self.sr |= bitZ

    def BMI(self):
        """ Branch if N = 1 """
        if self.sr & bitN:
            self.Branch()

    def BNE(self):
        """ Branch if Z = 0 """
        if not (self.sr & bitZ):
            self.Branch()

    def BPL(self):
        """ Branch on N = 0 """
        if not (self.sr & bitN):
            self.Branch()

    def BRK(self):
        """ Break """
        self.sr |= bitI | bitB
        self.memory[0x100 + self.sp] = self.pc >> 8
        self.memory[0x100 + self.sp-1] = self.pc & 0xFF
        self.memory[0x100 + self.sp-2] = self.sr
        self.sp -= 3

    def BVC(self):
        """ Branch on V = 0 """
        if not (self.sr & bitV):
            self.Branch()

    def BVS(self):
        """ Branch on V = 1 """
        if self.sr & bitV:
            self.Branch()

    """ SR clearing functions """
    def CLC(self):
        self.sr &= ~bitC

    def CLD(self):
        self.sr &= ~bitD

    def CLI(self):
        self.sr &= ~bitI

    def CLV(self):
        self.sr &= ~bitV

    def CMP(self):
        """ Compare memory with accumulator (A - M) """
        self.sr &= ~(bitN | bitZ | bitC)

        res = self.ac - self.GetValue()

        if res == 0:
            self.sr |= bitZ
        if res >= 0:
            self.sr |= bitC
        else:
            self.sr |= bitN

    def CPX(self):
        """ Compare memory with X register (X - M) """
        self.sr &= ~(bitN | bitZ | bitC)

        res = self.x - self.GetValue()

        if res == 0:
            self.sr |= bitZ
        if res >= 0:
            self.sr |= bitC
        else:
            self.sr |= bitN

    def CPY(self):
        """ Compare memory with Y register (Y - M) """
        self.sr &= ~(bitN | bitZ | bitC)

        res = self.y - self.GetValue()

        if res == 0:
            self.sr |= bitZ
        if res >= 0:
            self.sr |= bitC
        else:
            self.sr |= bitN

    def DEC(self):
        """ Decrement memory by 1 """
        self.sr &= ~(bitN | bitZ)

        val = (self.GetValue() - 1) % 0x100
        self.SetValue(val)

        self.CheckNZ(val)

    def DEX(self):
        """ Decrement X register """
        self.sr &= ~(bitN | bitZ)
        self.x -= 1
        self.CheckNZ(self.x)

    def DEY(self):
        """ Decrement Y register """
        self.sr &= ~(bitN | bitZ)
        self.y -= 1
        self.CheckNZ(self.y)

    def EOR(self):
        """ XOR memory with accumulator """
        self.sr &= ~(bitN | bitZ)
        self.ac ^= self.GetValue()
        self.CheckNZ(self.ac)

    def INC(self):
        """ Increment memory by 1 """
        self.sr &= ~(bitN | bitZ)

        val = (self.GetValue() + 1) % 0x100
        self.SetValue(val)

        self.CheckNZ(val)

    def INX(self):
        """ Increment X register """
        self.sr &= ~(bitN | bitZ)
        self.x += 1
        self.CheckNZ(self.x)

    def INY(self):
        """ Increment Y register """
        self.sr &= ~(bitN | bitZ)
        self.y += 1
        self.CheckNZ(self.y)

    def JMP(self):
        """ Jump to location (absolute or relative) """
        if self.amod == 'ind':
            # Gotta subtract 1 to make up for Core auto-incrementing
            pc = self.memory[self.arg1]
            pc += self.memory[self.arg1 + 1] << 8
            self.pc = pc - 1
        elif self.amod == 'abs':
            self.pc = self.arg1 - 1

    def JSR(self):
        """ Jump to location, saving PC on stack"""
        self.memory[0x100 + self.sp] = (self.pc & 0xFF00) >> 8
        self.memory[0x100 + self.sp - 1] = self.pc & 0xFF
        self.sp -= 2

        # Gotta subtract 1 to make up for Core auto-incrementing
        self.pc = self.arg1 - 1

    def LDA(self):
        """ Load accumulator with memory """
        self.sr &= ~(bitN | bitZ)
        self.ac = self.GetValue()
        self.CheckNZ(self.ac)

    def LDX(self):
        """ Load X register with memory """
        self.sr &= ~(bitN | bitZ)
        self.x = self.GetValue()
        self.CheckNZ(self.x)

    def LDY(self):
        """ Load Y register with memory """
        self.sr &= ~(bitN | bitZ)
        self.y = self.GetValue()
        self.CheckNZ(self.y)

    def LSR(self):
        """ Logical shift right memory or accumulator """
        self.sr &= ~(bitZ | bitC)

        if self.amod == 'A':
            if self.ac & 1:
                self.sr |= bitC
            self.ac >>= 1
            if self.ac == 0:
                self.sr |= bitZ

        else:
            val = self.GetValue()
            if val & 1:
                self.sr |= bitC
            val >>= 1
            if val == 0:
                self.sr |= bitZ
            self.SetValue(val)

    def NOP(self):
        """ No operation """
        pass

    def ORA(self):
        """ OR memory with accumulator """
        self.sr &= ~(bitN | bitZ)
        self.ac |= self.GetValue()
        self.CheckNZ(self.ac)

    def PHA(self):
        """ Push accumulator on stack """
        self.memory[0x100 + self.sp] = self.ac
        self.sp -= 1

    def PHP(self):
        """ Push SR on stack """
        self.memory[0x100 + self.sp] = self.sr
        self.sp -= 1

    def PLA(self):
        """ Pull accumulator from stack """
        self.sr &= ~(bitN | bitZ)

        self.sp += 1
        self.ac = self.memory[0x100 + self.sp]

        self.CheckNZ(self.ac)

    def PLP(self):
        """ Pull SR from stack """
        self.sp += 1
        self.sr = self.memory[0x100 + self.sp]

    def ROL(self):
        """ Rotate one bit left """
        self.sr &= ~(bitN | bitZ)

        carry = False
        if self.sr & bitC:
            carry = True

        val = 0
        if self.amod == 'A':
            val = self.ac
        else:
            val = self.GetValue()

        val <<= 1

        if val > 0xFF:
            val &= 0xFF
            self.sr |= bitC
        else:
            self.sr &= ~bitC

        if carry:
            val |= 1

        if self.amod == 'A':
            self.ac = val
        else:
            self.SetValue(val)

        self.CheckNZ(val)

    def ROR(self):
        """ Rotate one bit right """
        self.sr &= ~(bitN | bitZ)

        val = 0
        if self.amod == 'A':
            val = self.ac
        else:
            val = self.GetValue()

        carry = False
        if val & 1:
            carry = True

        val >>= 1

        if self.sr & bitC:
            val |= 0x80
            self.sr |= bitN

        if carry:
            self.sr |= bitC
        else:
            self.sr &= ~bitC

        if val == 0:
            self.sr |= bitZ

        if self.amod == 'A':
            self.ac = val
        else:
            self.SetValue(val)

    def RTI(self):
        """ Return from interrupt """
        self.sr = self.memory[0x100 + self.sp+1]
        pc = self.memory[0x100 + self.sp+2]
        pc += self.memory[0x100 + self.sp+3] << 8
        self.sp += 3
        self.pc = pc

    def RTS(self):
        """ Return from subroutine """
        pc = self.memory[0x100 + self.sp + 1]
        pc += self.memory[0x100 + self.sp + 2] << 8
        self.sp += 2
        self.pc = pc

    def SBC(self):
        """ Subtract memory from accumulator with carry A-M-(1-C) -> A """
        self.sr &= ~(bitN | bitZ | bitV)

        carry = 0 if (self.sr & bitC) else 1
        val = self.GetValue()
        self.ac -= (val + carry)

        if self.ac < 0:
            self.sr |= bitC | bitV
        else:
            self.sr &= ~bitC

        self.CheckNZ(self.ac)

    """ SR setting functions """
    def SEC(self):
        self.sr |= bitC

    def SED(self):
        self.sr |= bitD

    def SEI(self):
        self.sr |= bitI

    def STA(self):
        """ Store accumulator in memory """
        self.SetValue(self.ac)

    def STX(self):
        """ Store X register in memory """
        self.SetValue(self.x)

    def STY(self):
        """ Store Y register in memory """
        self.SetValue(self.y)

    def TAX(self):
        """ Transfer accumulator to X """
        self.sr &= ~(bitN | bitZ)
        self.x = self.ac
        self.CheckNZ(self.x)

    def TAY(self):
        """ Transfer accumulator to Y """
        self.sr &= ~(bitN | bitZ)

        self.y = self.ac
        self.CheckNZ(self.y)

    def TSX(self):
        """ Transfer stack pointer to X """
        self.sr &= ~(bitN | bitZ)

        self.x = self.sp
        self.CheckNZ(self.x)

    def TXA(self):
        """ Transfer X to accumulator """
        self.sr &= ~(bitN | bitZ)
        self.ac = self.x
        self.CheckNZ(self.ac)

    def TXS(self):
        """ Transfer X to stack pointer """
        self.sp = self.x

    def TYA(self):
        """ Transfer Y to accumulator """
        self.sr &= ~(bitN | bitZ)
        self.ac = self.y
        self.CheckNZ(self.ac)

    #----- Non-Instruction Functions -----#

    def CheckNZ(self, n):
        """ Check whether to set N and Z bits """
        if n < 0 or n > 0xFF:
            n &= 0xFF
        if n >= 0x80:
            self.sr |= bitN
        elif n == 0:
            self.sr |= bitZ

    def Branch(self):
        """ Branch to offset in arg1 (relative addressing mode) """
        if self.arg1 >= 0x80:
            offset = self.arg1 - 0x100
        else:
            offset = self.arg1
        self.pc += offset

    def GetValue(self):
        """ Get the value at the address specified by the current amod, arguments, and registers """
        if self.amod == '#':
            return self.arg1
        return self.memory[self.GetAddr()]

    def SetValue(self, val):
        """
        Sets the value at the address specified by the current amod, arguments, and registers
        Not to be used with immediate mode
        """
        if self.amod != '#':
            self.memory[self.GetAddr()] = val

    def GetAddr(self):
        """ Gets the address specified by the current amod, arguments, and registers """
        if self.amod in ['zpg', 'abs']:
            return self.arg1

        elif self.amod == 'zpg,x':
            return (self.arg1 + self.x) & 0xFF

        elif self.amod == 'abs,x':
            return self.arg1 + self.x

        elif self.amod == 'abs,y':
            return self.arg1 + self.y

        elif self.amod == 'x,ind':
            tgt = (self.x + self.arg1) & 0xFF
            return (self.memory[tgt + 1] << 8) + self.memory[tgt]

        elif self.amod == 'ind,y':
            tgt = self.arg1
            return (self.memory[tgt + 1] << 8) + self.memory[tgt] + self.y

        return -1




if __name__ == '__main__':
    if len(sys.argv) > 1:
        t = T34(sys.argv[1])
    else:
        t = T34()
    t.main()
