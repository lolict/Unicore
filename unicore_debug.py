#!/usr/bin/env python3
"""
UniCore Debugger - 交互式调试器
==============================
支持：单步执行、断点、寄存器查看、内存查看
"""

from unicore_vm import VM, Instruction, Opcode, Assembler
import sys


class Debugger:
    """UniCore 调试器"""
    
    def __init__(self, vm: VM = None):
        self.vm = vm or VM()
        self.assembler = Assembler()
        self.breakpoints = set()
        self.watchpoints = {}
        self.running = False
        self.source_map = {}
        
        self.commands = {
            'run': self.cmd_run,
            'r': self.cmd_run,
            'step': self.cmd_step,
            's': self.cmd_step,
            'next': self.cmd_step,
            'n': self.cmd_step,
            'break': self.cmd_break,
            'b': self.cmd_break,
            'delete': self.cmd_delete,
            'd': self.cmd_delete,
            'continue': self.cmd_run,
            'c': self.cmd_run,
            'print': self.cmd_print,
            'p': self.cmd_print,
            'info': self.cmd_info,
            'i': self.cmd_info,
            'registers': self.cmd_registers,
            'reg': self.cmd_registers,
            'memory': self.cmd_memory,
            'mem': self.cmd_memory,
            'x': self.cmd_memory,
            'disassemble': self.cmd_disasm,
            'dis': self.cmd_disasm,
            'assemble': self.cmd_assemble,
            'a': self.cmd_assemble,
            'load': self.cmd_load,
            'set': self.cmd_set,
            'watch': self.cmd_watch,
            'w': self.cmd_watch,
            'stack': self.cmd_stack,
            'st': self.cmd_stack,
            'backtrace': self.cmd_backtrace,
            'bt': self.cmd_backtrace,
            'help': self.cmd_help,
            'h': self.cmd_help,
            'quit': self.cmd_quit,
            'q': self.cmd_quit,
        }
    
    def load_program(self, program):
        """加载程序"""
        self.vm.load_program(program)
        print(f"✅ 程序已加载，共 {len(program)} 条指令")
        print(f"   入口地址: 0x{self.vm.pc:08x}")
    
    def load_source(self, source: str):
        """加载汇编源码"""
        program = self.assembler.assemble(source)
        self.load_program(program)
        
        lines = source.strip().split('\n')
        addr = 0x1000
        for line in lines:
            line = line.split(';')[0].strip()
            if line and not line.startswith('#'):
                self.source_map[addr] = line
                addr += 4
    
    def cmd_run(self, args):
        """运行程序"""
        if self.vm.halted:
            print("⚠️  程序已结束")
            return
        
        print("🚀 开始运行...")
        self.running = True
        
        while self.running and not self.vm.halted:
            if self.vm.pc in self.breakpoints:
                print(f"\n🔴 断点 at 0x{self.vm.pc:08x}")
                break
            
            self.vm.step()
            
            for addr, expr in self.watchpoints.items():
                val = self.vm.read_memory(addr)
                if val != expr.get('last', None):
                    print(f"\n👁️  Watchpoint at 0x{addr:08x}: {expr['last']} -> {val}")
                    expr['last'] = val
                    self.running = False
                    break
        
        if self.vm.halted:
            print("✅ 程序正常结束")
        else:
            print(f"\n⏸️  已暂停 at 0x{self.vm.pc:08x}")
        
        self.running = False
    
    def cmd_step(self, args):
        """单步执行"""
        if self.vm.halted:
            print("⚠️  程序已结束")
            return
        
        old_pc = self.vm.pc
        self.vm.step()
        
        print(f"→ PC: 0x{self.vm.pc:08x} ", end="")
        
        if self.vm.pc in self.source_map:
            print(f"│ {self.source_map[self.vm.pc]}")
        else:
            raw = self.vm.read_memory(old_pc, 4)
            inst = Instruction(
                Opcode(raw & 0xFF),
                (raw >> 8) & 0x3F,
                (raw >> 14) & 0x3F,
                (raw >> 20) & 0x3F,
                (raw >> 26) & 0x3F
            )
            print(f"│ {inst.op.name} R{inst.rd}, R{inst.rs}, R{inst.rt}, #{inst.imm}")
    
    def cmd_break(self, args):
        """设置断点"""
        if not args:
            print("用法: break <地址>")
            return
        
        try:
            if args.startswith('0x'):
                addr = int(args, 16)
            else:
                addr = int(args)
            
            self.breakpoints.add(addr)
            print(f"🔴 断点已设置 at 0x{addr:08x}")
        except ValueError:
            print(f"❌ 无效地址: {args}")
    
    def cmd_delete(self, args):
        """删除断点"""
        if not args:
            print("用法: delete <地址>")
            return
        
        try:
            if args.startswith('0x'):
                addr = int(args, 16)
            else:
                addr = int(args)
            
            if addr in self.breakpoints:
                self.breakpoints.remove(addr)
                print(f"🗑️  断点已删除 at 0x{addr:08x}")
            else:
                print(f"⚠️  断点不存在")
        except ValueError:
            print(f"❌ 无效地址: {args}")
    
    def cmd_print(self, args):
        """打印表达式"""
        if not args:
            self.cmd_registers(None)
            return
        
        for expr in args.split(','):
            expr = expr.strip()
            
            if expr.startswith('R') or expr.startswith('r'):
                try:
                    idx = int(expr[1:])
                    print(f"  {expr} = {self.vm.registers[idx]}")
                except:
                    pass
            elif expr == 'PC':
                print(f"  PC = 0x{self.vm.pc:08x}")
            elif expr == 'SP':
                print(f"  SP = 0x{self.vm.sp:08x}")
            elif expr == 'cycles':
                print(f"  Cycles = {self.vm.cycles}")
    
    def cmd_registers(self, args):
        """显示寄存器"""
        print("\n📊 寄存器状态:")
        print(f"  PC = 0x{self.vm.pc:08x}")
        print(f"  SP = 0x{self.vm.sp:08x}")
        print(f"  Cycles = {self.vm.cycles}")
        print()
        
        for i in range(0, min(16, 64), 4):
            line = "  "
            for j in range(4):
                if i + j < 64:
                    line += f"R{i+j:02d}={self.vm.registers[i+j]:12d}  "
            print(line)
    
    def cmd_memory(self, args):
        """显示内存"""
        addr = 0x1000
        count = 8
        
        if args:
            parts = args.split()
            try:
                if parts[0].startswith('0x'):
                    addr = int(parts[0], 16)
                else:
                    addr = int(parts[0])
                if len(parts) > 1:
                    count = int(parts[1])
            except ValueError:
                print(f"❌ 无效参数")
                return
        
        print(f"\n📍 内存 dump at 0x{addr:08x} (共 {count} 条):")
        print()
        
        for i in range(count):
            a = addr + i * 8
            val = self.vm.read_memory(a)
            print(f"  0x{a:08x}: 0x{val:016x}  ({val})")
    
    def cmd_disasm(self, args):
        """反汇编"""
        addr = self.vm.pc
        count = 10
        
        if args:
            parts = args.split()
            try:
                if parts[0].startswith('0x'):
                    addr = int(parts[0], 16)
                else:
                    addr = int(parts[0])
                if len(parts) > 1:
                    count = int(parts[1])
            except ValueError:
                print(f"❌ 无效参数")
                return
        
        print(f"\n📍 反汇编 at 0x{addr:08x} (共 {count} 条):")
        print()
        
        for i in range(count):
            raw = self.vm.read_memory(addr, 4)
            inst = Instruction(
                Opcode(raw & 0xFF),
                (raw >> 8) & 0x3F,
                (raw >> 14) & 0x3F,
                (raw >> 20) & 0x3F,
                (raw >> 26) & 0x3F
            )
            
            marker = "→" if addr == self.vm.pc else " "
            marker += "●" if addr in self.breakpoints else " "
            
            print(f"  {marker} 0x{addr:08x}: {inst.op.name:8} R{inst.rd:02d}, R{inst.rs:02d}, R{inst.rt:02d}, #{inst.imm:02d}")
            addr += 4
    
    def cmd_assemble(self, args):
        """内联汇编"""
        if not args:
            print("用法: assemble <指令>")
            return
        
        try:
            program = self.assembler.assemble(args)
            if program:
                inst = program[0]
                print(f"  {inst.op.name} R{inst.rd}, R{inst.rs}, R{inst.rt}, #{inst.imm}")
        except Exception as e:
            print(f"❌ 汇编错误: {e}")
    
    def cmd_set(self, args):
        """设置寄存器/内存"""
        if not args:
            print("用法: set <寄存器>=<值> 或 set *<地址>=<值>")
            return
        
        try:
            if '=' in args:
                lhs, rhs = args.split('=', 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                val = int(rhs)
                
                if lhs.startswith('R') or lhs.startswith('r'):
                    idx = int(lhs[1:])
                    self.vm.registers[idx] = val
                    print(f"  {lhs} = {val}")
                elif lhs.startswith('*0x'):
                    addr = int(lhs[2:], 16)
                    self.vm.write_memory(addr, val)
                    print(f"  *0x{addr:08x} = {val}")
        except Exception as e:
            print(f"❌ 设置错误: {e}")
    
    def cmd_watch(self, args):
        """设置监视点"""
        if not args:
            print("监视点:")
            for addr, expr in self.watchpoints.items():
                print(f"  *0x{addr:08x}")
            return
        
        try:
            if args.startswith('0x'):
                addr = int(args, 16)
            else:
                addr = int(args)
            
            self.watchpoints[addr] = {'last': self.vm.read_memory(addr)}
            print(f"👁️  监视点已设置 at 0x{addr:08x}")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    def cmd_stack(self, args):
        """显示栈"""
        print("\n📍 栈内容:")
        sp = self.vm.sp
        for i in range(8):
            addr = sp + i * 8
            val = self.vm.read_memory(addr)
            print(f"  0x{addr:08x}: 0x{val:016x}  ({val})")
    
    def cmd_backtrace(self, args):
        """回溯"""
        print("\n📍 调用栈:")
        print(f"  SP = 0x{self.vm.sp:08x}")
        print(f"  PC = 0x{self.vm.pc:08x}")
        print(f"  R63 (LR) = 0x{self.vm.registers[63]:08x}")
    
    def cmd_help(self, args):
        """帮助"""
        print("""
╔════════════════════════════════════════════════════════════╗
║                    UniCore Debugger                    ║
╚════════════════════════════════════════════════════════════╝

运行控制:
  run/r          - 运行程序
  step/s/n       - 单步执行
  continue/c     - 继续运行
  quit/q         - 退出

断点:
  break <addr>   - 设置断点
  delete <addr>  - 删除断点

查看:
  registers/reg  - 显示寄存器
  memory <addr>  - 显示内存
  disassemble/dis - 反汇编
  stack/st       - 显示栈
  backtrace/bt   - 回溯

修改:
  set R<n>=<val> - 设置寄存器
  set *<addr>=<val> - 设置内存
  watch <addr>    - 设置监视点

其他:
  assemble <asm>  - 内联汇编
  print <expr>    - 打印表达式
  help/h          - 显示帮助
        """)
    
    def cmd_quit(self, args):
        """退出"""
        print("👋 再见！")
        sys.exit(0)
    
    def cmd_info(self, args):
        """信息"""
        print(f"\n📊 程序信息:")
        print(f"  断点: {len(self.breakpoints)}")
        print(f"  监视点: {len(self.watchpoints)}")
        print(f"  周期: {self.vm.cycles}")
        print(f"  状态: {'已结束' if self.vm.halted else '运行中'}")
    
    def cmd_load(self, args):
        """加载程序"""
        if not args:
            print("用法: load <文件>")
            return
        
        try:
            with open(args, 'r') as f:
                source = f.read()
            self.load_source(source)
        except Exception as e:
            print(f"❌ 加载错误: {e}")
    
    def run(self):
        """运行调试器"""
        print("""
╔════════════════════════════════════════════════════════════╗
║              UniCore Debugger - 交互式调试器             ║
╚════════════════════════════════════════════════════════════╝
输入 'help' 查看帮助
        """)
        
        while True:
            try:
                cmd = input(f"unicore dbg (0x{self.vm.pc:08x})> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split(None, 1)
                name = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if name in self.commands:
                    self.commands[name](args)
                else:
                    print(f"❌ 未知命令: {name}")
            
            except KeyboardInterrupt:
                print("\n⌨️  Ctrl+C - 使用 'quit' 退出")
            except EOFError:
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def main():
    debugger = Debugger()
    
    demo_code = """
    MOVI R1, 5
    MOVI R2, 3
    ADD R3, R1, R2
    SUB R4, R1, R2
    MUL R5, R3, R4
    HALT
    """
    
    print("📝 加载演示程序...")
    debugger.load_source(demo_code)
    
    print("\n🔍 调试器已启动")
    debugger.cmd_help(None)
    
    debugger.run()


if __name__ == "__main__":
    main()
