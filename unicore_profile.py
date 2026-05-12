#!/usr/bin/env python3
"""
UniCore Profiler - 性能分析器
==============================
统计指令执行频率、性能瓶颈分析
"""

from unicore_vm import VM, Instruction, Opcode, Assembler
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List
import time


@dataclass
class InstructionStats:
    """指令统计"""
    count: int = 0
    total_cycles: int = 0
    min_cycles: int = 0
    max_cycles: int = 0


@dataclass 
class FunctionStats:
    """函数统计"""
    name: str
    call_count: int = 0
    total_cycles: int = 0
    instructions: int = 0


class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self.vm = VM()
        self.assembler = Assembler()
        self.instr_stats: Dict[Opcode, InstructionStats] = {}
        self.branch_stats = {"taken": 0, "not_taken": 0}
        self.memory_access = {"loads": 0, "stores": 0}
        self.cycles_by_function: Dict[str, int] = {}
        self.call_stack: List[str] = []
        self.current_function = "main"
        self.start_time = 0
        self.end_time = 0
        
        for op in Opcode:
            self.instr_stats[op] = InstructionStats()
    
    def profile_instruction(self, inst: Instruction):
        """分析单条指令"""
        op = inst.op
        
        stats = self.instr_stats[op]
        stats.count += 1
        
        cycles = self._get_instruction_cycles(op)
        stats.total_cycles += cycles
        if stats.min_cycles == 0:
            stats.min_cycles = cycles
        stats.max_cycles = max(stats.max_cycles, cycles)
    
    def _get_instruction_cycles(self, op: Opcode) -> int:
        """获取指令周期数"""
        cycles = {
            Opcode.NOP: 1,
            Opcode.ADD: 1,
            Opcode.SUB: 1,
            Opcode.MUL: 3,
            Opcode.DIV: 10,
            Opcode.AND: 1,
            Opcode.OR: 1,
            Opcode.XOR: 1,
            Opcode.MOV: 1,
            Opcode.MOVI: 1,
            Opcode.LOAD: 5,
            Opcode.STORE: 5,
            Opcode.JMP: 2,
            Opcode.JE: 2,
            Opcode.JNE: 2,
            Opcode.CALL: 3,
            Opcode.RET: 2,
            Opcode.PUSH: 2,
            Opcode.POP: 2,
            Opcode.CMP: 1,
            Opcode.SYSCALL: 100,
            Opcode.HALT: 1,
        }
        return cycles.get(op, 1)
    
    def step(self) -> bool:
        """单步执行并分析"""
        if self.vm.halted:
            return False
        
        raw = self.vm.read_memory(self.vm.pc, 4)
        inst = Instruction(
            Opcode(raw & 0xFF),
            (raw >> 8) & 0x3F,
            (raw >> 14) & 0x3F,
            (raw >> 20) & 0x3F,
            (raw >> 26) & 0x3F
        )
        
        self.vm.pc += 4
        self.vm.cycles += 1
        
        self.profile_instruction(inst)
        
        op = inst.op
        
        if op == Opcode.ADD:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] + self.vm.registers[inst.rt]
        elif op == Opcode.SUB:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] - self.vm.registers[inst.rt]
        elif op == Opcode.MUL:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] * self.vm.registers[inst.rt]
        elif op == Opcode.DIV:
            if self.vm.registers[inst.rt] != 0:
                self.vm.registers[inst.rd] = self.vm.registers[inst.rs] // self.vm.registers[inst.rt]
        elif op == Opcode.AND:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] & self.vm.registers[inst.rt]
        elif op == Opcode.OR:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] | self.vm.registers[inst.rt]
        elif op == Opcode.XOR:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs] ^ self.vm.registers[inst.rt]
        elif op == Opcode.MOV:
            self.vm.registers[inst.rd] = self.vm.registers[inst.rs]
        elif op == Opcode.MOVI:
            self.vm.registers[inst.rd] = inst.imm
        elif op == Opcode.LOAD:
            addr = self.vm.registers[inst.rs] + inst.imm
            self.vm.registers[inst.rd] = self.vm.read_memory(addr)
            self.memory_access["loads"] += 1
        elif op == Opcode.STORE:
            addr = self.vm.registers[inst.rd] + inst.imm
            self.vm.write_memory(addr, self.vm.registers[inst.rs])
            self.memory_access["stores"] += 1
        elif op == Opcode.JMP:
            self.vm.pc = inst.imm * 4
            self.branch_stats["taken"] += 1
        elif op == Opcode.JE:
            if self.vm.flags == 0:
                self.vm.pc = inst.imm * 4
                self.branch_stats["taken"] += 1
            else:
                self.branch_stats["not_taken"] += 1
        elif op == Opcode.JNE:
            if self.vm.flags != 0:
                self.vm.pc = inst.imm * 4
                self.branch_stats["taken"] += 1
            else:
                self.branch_stats["not_taken"] += 1
        elif op == Opcode.CALL:
            self.vm.registers[63] = self.vm.pc
            self.vm.pc = inst.imm * 4
            self.branch_stats["taken"] += 1
        elif op == Opcode.RET:
            self.vm.pc = self.vm.registers[63]
        elif op == Opcode.PUSH:
            self.vm.sp -= 8
            self.vm.write_memory(self.vm.sp, self.vm.registers[inst.rd])
        elif op == Opcode.POP:
            self.vm.registers[inst.rd] = self.vm.read_memory(self.vm.sp)
            self.vm.sp += 8
        elif op == Opcode.CMP:
            diff = self.vm.registers[inst.rs] - self.vm.registers[inst.rt]
            self.vm.flags = 0 if diff == 0 else (1 if diff < 0 else 2)
        elif op == Opcode.HALT:
            self.vm.halted = True
        elif op == Opcode.SYSCALL:
            pass
        
        return not self.vm.halted
    
    def run(self, program: List[Instruction], max_cycles: int = 100000) -> int:
        """运行并分析"""
        self.start_time = time.time()
        self.vm.load_program(program)
        
        cycles = 0
        while not self.vm.halted and cycles < max_cycles:
            self.step()
            cycles += 1
        
        self.end_time = time.time()
        return cycles
    
    def load_and_run(self, source: str, max_cycles: int = 100000) -> int:
        """加载并运行"""
        program = self.assembler.assemble(source)
        return self.run(program, max_cycles)
    
    def get_report(self) -> str:
        """生成报告"""
        total_instr = sum(s.count for s in self.instr_stats.values())
        total_cycles = sum(s.total_cycles for s in self.instr_stats.values())
        elapsed = self.end_time - self.start_time
        
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("                   UniCore 性能分析报告")
        lines.append("=" * 70)
        
        lines.append("\n📊 总体统计:")
        lines.append(f"  总指令数:    {total_instr}")
        lines.append(f"  总周期数:    {total_cycles}")
        lines.append(f"  执行时间:    {elapsed*1000:.3f} ms")
        lines.append(f"  平均 CPI:    {total_cycles/total_instr:.2f} 周期/指令")
        
        if elapsed > 0:
            lines.append(f"  模拟速度:    {int(total_cycles/elapsed):,} 周期/秒")
        
        lines.append("\n📈 指令执行统计:")
        lines.append("-" * 70)
        lines.append(f"  {'指令':<10} {'次数':<10} {'占比':<10} {'总周期':<10} {'平均':<8}")
        lines.append("-" * 70)
        
        sorted_stats = sorted(
            [(op, stats) for op, stats in self.instr_stats.items() if stats.count > 0],
            key=lambda x: x[1].count,
            reverse=True
        )
        
        for op, stats in sorted_stats[:15]:
            pct = (stats.count / total_instr) * 100 if total_instr > 0 else 0
            avg = stats.total_cycles / stats.count if stats.count > 0 else 0
            lines.append(f"  {op.name:<10} {stats.count:<10} {pct:>6.2f}%    {stats.total_cycles:<10} {avg:<8.2f}")
        
        lines.append("\n💾 内存访问:")
        lines.append(f"  Load:  {self.memory_access['loads']}")
        lines.append(f"  Store: {self.memory_access['stores']}")
        lines.append(f"  总计:   {self.memory_access['loads'] + self.memory_access['stores']}")
        
        lines.append("\n🔀 分支预测:")
        total_branches = self.branch_stats["taken"] + self.branch_stats["not_taken"]
        if total_branches > 0:
            taken_pct = (self.branch_stats["taken"] / total_branches) * 100
            lines.append(f"  Taken:      {self.branch_stats['taken']} ({taken_pct:.1f}%)")
            lines.append(f"  Not Taken: {self.branch_stats['not_taken']} ({100-taken_pct:.1f}%)")
        
        lines.append("\n⚠️  性能瓶颈:")
        sorted_by_cycles = sorted(
            [(op, stats) for op, stats in self.instr_stats.items() if stats.count > 0],
            key=lambda x: x[1].total_cycles,
            reverse=True
        )
        
        if sorted_by_cycles:
            top = sorted_by_cycles[0]
            lines.append(f"  最多周期: {top[0].name} ({top[1].total_cycles} 周期, {top[1].count} 次)")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════════╗
║              UniCore Profiler - 性能分析器             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    profiler = Profiler()
    
    code = """
    MOVI R1, 1
    MOVI R2, 100
    
    loop:
    ADD R3, R3, R1
    ADDI R1, R1, 1
    CMP R1, R2
    JNE loop
    
    HALT
    """
    
    print("📝 分析程序: 1+2+3+...+100")
    print("🚀 运行中...")
    
    cycles = profiler.load_and_run(code)
    
    print(profiler.get_report())
    
    print(f"\n✅ 分析完成!")
    print(f"   计算结果: R3 = {profiler.vm.registers[3]}")


if __name__ == "__main__":
    demo()
