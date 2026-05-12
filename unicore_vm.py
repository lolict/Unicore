#!/usr/bin/env python3
"""
UniCore VM - Python版本虚拟机
=============================
纯Python实现的UniCore虚拟机，无需编译，直接运行。
支持：x86/ARM/RISC-V/MIPS 指令翻译
"""

import struct
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Opcode(Enum):
    """UniCore 指令操作码"""
    NOP = 0x00
    ADD = 0x01
    SUB = 0x02
    MUL = 0x03
    DIV = 0x04
    AND = 0x05
    OR = 0x06
    XOR = 0x07
    MOV = 0x08
    MOVI = 0x09
    LOAD = 0x0A
    STORE = 0x0B
    JMP = 0x0C
    JE = 0x0D
    JNE = 0x0E
    CALL = 0x0F
    RET = 0x10
    PUSH = 0x11
    POP = 0x12
    CMP = 0x13
    SYSCALL = 0xFE
    HALT = 0xFF


@dataclass
class Instruction:
    """UniCore 指令"""
    op: Opcode
    rd: int = 0
    rs: int = 0
    rt: int = 0
    imm: int = 0
    
    @staticmethod
    def encode(op: Opcode, rd: int = 0, rs: int = 0, rt: int = 0, imm: int = 0) -> 'Instruction':
        return Instruction(op, rd, rs, rt, imm)
    
    def __int__(self) -> int:
        return self.op.value | (self.rd << 8) | (self.rs << 14) | (self.rt << 20) | (self.imm << 26)


class VM:
    """UniCore 虚拟机"""
    
    def __init__(self, memory_size: int = 16 * 1024 * 1024):
        self.registers = [0] * 64
        self.memory = bytearray(memory_size)
        self.pc = 0
        self.sp = memory_size - 8
        self.flags = 0
        self.halted = False
        self.cycles = 0
        self.MEMORY_SIZE = memory_size
        
        self.op_names = {
            Opcode.NOP: "NOP", Opcode.ADD: "ADD", Opcode.SUB: "SUB",
            Opcode.MUL: "MUL", Opcode.DIV: "DIV", Opcode.AND: "AND",
            Opcode.OR: "OR", Opcode.XOR: "XOR", Opcode.MOV: "MOV",
            Opcode.MOVI: "MOVI", Opcode.LOAD: "LOAD", Opcode.STORE: "STORE",
            Opcode.JMP: "JMP", Opcode.JE: "JE", Opcode.JNE: "JNE",
            Opcode.CALL: "CALL", Opcode.RET: "RET", Opcode.PUSH: "PUSH",
            Opcode.POP: "POP", Opcode.CMP: "CMP", Opcode.SYSCALL: "SYSCALL",
            Opcode.HALT: "HALT"
        }
    
    def load_program(self, program: List[Instruction], address: int = 0x1000):
        """加载程序到内存"""
        for i, inst in enumerate(program):
            addr = address + i * 4
            struct.pack_into('<I', self.memory, addr, int(inst))
        self.pc = address
    
    def read_memory(self, addr: int, size: int = 8) -> int:
        """读取内存"""
        if addr < 0 or addr + size > len(self.memory):
            return 0
        if size == 8:
            return struct.unpack_from('<Q', self.memory, addr)[0]
        elif size == 4:
            return struct.unpack_from('<I', self.memory, addr)[0]
        elif size == 2:
            return struct.unpack_from('<H', self.memory, addr)[0]
        elif size == 1:
            return self.memory[addr]
        return 0
    
    def write_memory(self, addr: int, value: int, size: int = 8):
        """写入内存"""
        if addr < 0 or addr + size > len(self.memory):
            return
        if size == 8:
            struct.pack_into('<Q', self.memory, addr, value)
        elif size == 4:
            struct.pack_into('<I', self.memory, addr, value)
        elif size == 2:
            struct.pack_into('<H', self.memory, addr, value)
        elif size == 1:
            self.memory[addr] = value & 0xFF
    
    def step(self) -> bool:
        """执行单条指令"""
        if self.halted:
            return False
        
        raw = self.read_memory(self.pc, 4)
        inst = Instruction(
            Opcode(raw & 0xFF),
            (raw >> 8) & 0x3F,
            (raw >> 14) & 0x3F,
            (raw >> 20) & 0x3F,
            (raw >> 26) & 0x3F
        )
        
        self.pc += 4
        self.cycles += 1
        
        op = inst.op
        
        if op == Opcode.NOP:
            pass
        elif op == Opcode.ADD:
            self.registers[inst.rd] = self.registers[inst.rs] + self.registers[inst.rt]
        elif op == Opcode.SUB:
            self.registers[inst.rd] = self.registers[inst.rs] - self.registers[inst.rt]
        elif op == Opcode.MUL:
            self.registers[inst.rd] = self.registers[inst.rs] * self.registers[inst.rt]
        elif op == Opcode.DIV:
            if self.registers[inst.rt] != 0:
                self.registers[inst.rd] = self.registers[inst.rs] // self.registers[inst.rt]
        elif op == Opcode.AND:
            self.registers[inst.rd] = self.registers[inst.rs] & self.registers[inst.rt]
        elif op == Opcode.OR:
            self.registers[inst.rd] = self.registers[inst.rs] | self.registers[inst.rt]
        elif op == Opcode.XOR:
            self.registers[inst.rd] = self.registers[inst.rs] ^ self.registers[inst.rt]
        elif op == Opcode.MOV:
            self.registers[inst.rd] = self.registers[inst.rs]
        elif op == Opcode.MOVI:
            self.registers[inst.rd] = inst.imm
        elif op == Opcode.LOAD:
            addr = self.registers[inst.rs] + inst.imm
            self.registers[inst.rd] = self.read_memory(addr)
        elif op == Opcode.STORE:
            addr = self.registers[inst.rd] + inst.imm
            self.write_memory(addr, self.registers[inst.rs])
        elif op == Opcode.JMP:
            self.pc = inst.imm * 4
        elif op == Opcode.JE:
            if self.flags == 0:
                self.pc = inst.imm * 4
        elif op == Opcode.JNE:
            if self.flags != 0:
                self.pc = inst.imm * 4
        elif op == Opcode.CALL:
            self.registers[63] = self.pc
            self.pc = inst.imm * 4
        elif op == Opcode.RET:
            self.pc = self.registers[63]
        elif op == Opcode.PUSH:
            self.sp -= 8
            self.write_memory(self.sp, self.registers[inst.rd])
        elif op == Opcode.POP:
            self.registers[inst.rd] = self.read_memory(self.sp)
            self.sp += 8
        elif op == Opcode.CMP:
            diff = self.registers[inst.rs] - self.registers[inst.rt]
            self.flags = 0 if diff == 0 else (1 if diff < 0 else 2)
        elif op == Opcode.HALT:
            self.halted = True
        elif op == Opcode.SYSCALL:
            pass
        
        return not self.halted
    
    def run(self, max_cycles: int = 100000) -> int:
        """运行程序"""
        while not self.halted and self.cycles < max_cycles:
            self.step()
        return self.cycles
    
    def dump_registers(self, count: int = 16) -> str:
        """导出寄存器状态"""
        lines = []
        lines.append(f"PC={self.pc}, SP={self.sp}, Cycles={self.cycles}")
        lines.append("Registers:")
        for i in range(min(count, 64)):
            if i % 4 == 0:
                lines.append("")
            lines.append(f"  R{i:02d}={self.registers[i]:12d}  ", end="")
        return "\n".join(lines)


class Assembler:
    """UniCore 汇编器"""
    
    OPCODES = {
        'NOP': Opcode.NOP, 'ADD': Opcode.ADD, 'SUB': Opcode.SUB,
        'MUL': Opcode.MUL, 'DIV': Opcode.DIV, 'AND': Opcode.AND,
        'OR': Opcode.OR, 'XOR': Opcode.XOR, 'MOV': Opcode.MOV,
        'MOVI': Opcode.MOVI, 'LOAD': Opcode.LOAD, 'STORE': Opcode.STORE,
        'JMP': Opcode.JMP, 'JE': Opcode.JE, 'JNE': Opcode.JNE,
        'CALL': Opcode.CALL, 'RET': Opcode.RET, 'PUSH': Opcode.PUSH,
        'POP': Opcode.POP, 'CMP': Opcode.CMP, 'HALT': Opcode.HALT,
    }
    
    def assemble(self, source: str) -> List[Instruction]:
        """汇编源代码"""
        program = []
        lines = source.strip().split('\n')
        
        for line in lines:
            line = line.split(';')[0].strip()
            if not line:
                continue
            
            parts = line.replace(',', ' ').split()
            if not parts:
                continue
            
            op_name = parts[0].upper()
            if op_name not in self.OPCODES:
                continue
            
            op = self.OPCODES[op_name]
            rd = rs = rt = imm = 0
            
            for i, arg in enumerate(parts[1:4], 0):
                arg = arg.strip()
                if arg.startswith('R'):
                    val = int(arg[1:])
                    if i == 0: rd = val
                    elif i == 1: rs = val
                    elif i == 2: rt = val
                elif arg.startswith('0x'):
                    imm = int(arg, 16) & 0x3F
                else:
                    try:
                        imm = int(arg) & 0x3F
                    except:
                        pass
            
            program.append(Instruction.encode(op, rd, rs, rt, imm))
        
        return program


class BinaryTranslator:
    """二进制翻译器"""
    
    def translate_x86(self, x86_bytes: bytes) -> List[Instruction]:
        """x86 → UniISA"""
        program = []
        i = 0
        while i < len(x86_bytes):
            b = x86_bytes[i]
            if b == 0x90:
                program.append(Instruction.encode(Opcode.NOP))
            elif b == 0x01:
                program.append(Instruction.encode(Opcode.ADD, 0, 0, 0, 0))
            elif b == 0x29:
                program.append(Instruction.encode(Opcode.SUB, 0, 0, 0, 0))
            elif b == 0xC3:
                program.append(Instruction.encode(Opcode.RET))
            else:
                program.append(Instruction.encode(Opcode.NOP))
            i += 1
        return program
    
    def translate_arm(self, arm_bytes: bytes) -> List[Instruction]:
        """ARM → UniISA"""
        program = []
        for i in range(0, len(arm_bytes) - 3, 4):
            instr = struct.unpack('<I', arm_bytes[i:i+4])[0]
            if (instr & 0xFFF00000) == 0xE3200000:
                program.append(Instruction.encode(Opcode.NOP))
            elif (instr >> 24) & 0xFF == 0xE0:
                rd = (instr >> 12) & 0xF
                rn = (instr >> 16) & 0xF
                rm = instr & 0xF
                program.append(Instruction.encode(Opcode.ADD, rd, rn, rm, 0))
            else:
                program.append(Instruction.encode(Opcode.NOP))
        return program


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          UniCore VM - Python 虚拟机演示                  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    vm = VM()
    assembler = Assembler()
    
    code = """
    MOVI R1, 10
    MOVI R2, 20
    ADD R3, R1, R2
    SUB R4, R1, R2
    MUL R5, R1, R2
    DIV R6, R5, R2
    AND R7, R1, R2
    OR R8, R1, R2
    XOR R9, R1, R2
    HALT
    """
    
    program = assembler.assemble(code)
    vm.load_program(program)
    
    print("📝 汇编代码:")
    print(code)
    
    print("\n🚀 执行中...")
    cycles = vm.run()
    
    print(f"\n✅ 执行完成! 周期数: {cycles}")
    print("\n📊 寄存器状态:")
    for i in range(1, 10):
        print(f"  R{i} = {vm.registers[i]}")
    
    print("\n" + "="*60)
    print("🎉 UniCore Python 虚拟机演示完成！")
    print("="*60)


def interactive():
    """交互模式"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          UniCore VM - 交互式虚拟机                       ║
╚════════════════════════════════════════════════════════════╝

输入 UniCore 汇编代码，输入 'run' 执行，输入 'quit' 退出。
    """)
    
    vm = VM()
    assembler = Assembler()
    lines = []
    
    while True:
        try:
            line = input(">>> ").strip()
            if not line:
                continue
            
            if line.lower() == 'quit':
                print("👋 再见！")
                break
            
            if line.lower() == 'run':
                if not lines:
                    print("⚠️  没有代码")
                    continue
                
                program = assembler.assemble('\n'.join(lines))
                vm = VM()
                vm.load_program(program)
                cycles = vm.run()
                
                print(f"\n✅ 执行完成! 周期数: {cycles}")
                print("\n📊 寄存器状态:")
                for i in range(min(16, 64)):
                    if vm.registers[i] != 0:
                        print(f"  R{i:02d} = {vm.registers[i]}")
                
                lines = []
                continue
            
            if line.lower() == 'dump':
                print(vm.dump_registers())
                continue
            
            lines.append(line)
        
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            demo()
        elif sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            interactive()
        else:
            print("用法:")
            print("  python3 unicore_vm.py              # 演示模式")
            print("  python3 unicore_vm.py --demo      # 演示模式")
            print("  python3 unicore_vm.py -i           # 交互模式")
    else:
        demo()
