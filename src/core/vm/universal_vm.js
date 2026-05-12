/**
 * UniCore Universal VM - 通用虚拟机
 * 完全自主的指令集虚拟机，兼容所有平台
 */

class UniversalVM {
    constructor() {
        // 通用寄存器 R0-R63
        this.registers = new BigUint64Array(64);
        // 向量寄存器 V0-V31
        this.vectorRegisters = new Float32Array(32 * 8);
        // 控制寄存器
        this.controlRegisters = new BigUint64Array(16);
        // 特殊寄存器
        this.PC = 0;      // 程序计数器
        this.SP = 0;      // 栈指针
        this.HP = 0;      // 堆指针
        this.ZF = 0;      // 零标志
        this.CF = 0;      // 进位标志
        this.OF = 0;      // 溢出标志
        this.SF = 0;      // 符号标志
        this.PF = 0;      // 奇偶标志
        
        // 内存 (16MB虚拟空间)
        this.memorySize = 16 * 1024 * 1024;
        this.memory = new Uint8Array(this.memorySize);
        
        // 状态
        this.running = false;
        this.mode = 'user'; // user/kernel/vm/debug
        
        // 线程管理
        this.threads = new Map();
        this.currentThread = 0;
        
        // 中断处理
        this.interrupts = new Map();
        
        // 指令定义
        this.instructions = this.initInstructions();
        
        // 性能统计
        this.stats = {
            instructions: 0,
            cycles: 0,
            cacheHits: 0,
            cacheMisses: 0
        };
    }

    initInstructions() {
        return {
            // 0x00-0x0F: 算术运算
            0x00: { name: 'NOP', execute: () => {} },
            0x01: { name: 'ADD', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) + this.regGet(rb)) },
            0x02: { name: 'SUB', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) - this.regGet(rb)) },
            0x03: { name: 'MUL', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) * this.regGet(rb)) },
            0x04: { name: 'DIV', execute: (rd, ra, rb) => {
                const b = this.regGet(rb);
                if (b !== 0n) this.regSet(rd, this.regGet(ra) / b);
            }},
            0x05: { name: 'MOD', execute: (rd, ra, rb) => {
                const b = this.regGet(rb);
                if (b !== 0n) this.regSet(rd, this.regGet(ra) % b);
            }},
            0x06: { name: 'NEG', execute: (rd, ra) => this.regSet(rd, -this.regGet(ra)) },
            0x07: { name: 'INC', execute: (rd) => this.regSet(rd, this.regGet(rd) + 1n) },
            0x08: { name: 'DEC', execute: (rd) => this.regSet(rd, this.regGet(rd) - 1n) },
            0x09: { name: 'ADC', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) + this.regGet(rb) + BigInt(this.CF)) },
            
            // 0x10-0x1F: 位运算
            0x10: { name: 'AND', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) & this.regGet(rb)) },
            0x11: { name: 'OR', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) | this.regGet(rb)) },
            0x12: { name: 'XOR', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) ^ this.regGet(rb)) },
            0x13: { name: 'NOT', execute: (rd, ra) => this.regSet(rd, ~this.regGet(ra)) },
            0x14: { name: 'SHL', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) << this.regGet(rb)) },
            0x15: { name: 'SHR', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) >> this.regGet(rb)) },
            0x16: { name: 'SAR', execute: (rd, ra, rb) => this.regSet(rd, BigInt.asIntN(64, this.regGet(ra) >> this.regGet(rb))) },
            0x17: { name: 'ROL', execute: (rd, ra, rb) => {
                const val = this.regGet(ra);
                const sh = Number(this.regGet(rb) & 63n);
                this.regSet(rd, (val << BigInt(sh)) | (val >> BigInt(64 - sh)));
            }},
            0x18: { name: 'ROR', execute: (rd, ra, rb) => {
                const val = this.regGet(ra);
                const sh = Number(this.regGet(rb) & 63n);
                this.regSet(rd, (val >> BigInt(sh)) | (val << BigInt(64 - sh)));
            }},
            
            // 0x20-0x2F: 比较指令
            0x20: { name: 'CMP', execute: (ra, rb) => {
                const a = this.regGet(ra), b = this.regGet(rb);
                this.ZF = a === b ? 1 : 0;
                this.SF = a < b ? 1 : 0;
                this.OF = 0;
            }},
            0x21: { name: 'CMPEQ', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) === this.regGet(rb) ? 1n : 0n) },
            0x22: { name: 'CMPLT', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) < this.regGet(rb) ? 1n : 0n) },
            0x23: { name: 'CMPLE', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) <= this.regGet(rb) ? 1n : 0n) },
            0x24: { name: 'CMPGT', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) > this.regGet(rb) ? 1n : 0n) },
            0x25: { name: 'CMPGE', execute: (rd, ra, rb) => this.regSet(rd, this.regGet(ra) >= this.regGet(rb) ? 1n : 0n) },
            
            // 0x30-0x3F: 控制流
            0x30: { name: 'JMP', execute: (addr) => this.PC = Number(addr) },
            0x31: { name: 'JZ', execute: (addr) => { if (this.ZF) this.PC = Number(addr); }},
            0x32: { name: 'JNZ', execute: (addr) => { if (!this.ZF) this.PC = Number(addr); }},
            0x33: { name: 'JE', execute: (addr) => { if (this.ZF) this.PC = Number(addr); }},
            0x34: { name: 'JNE', execute: (addr) => { if (!this.ZF) this.PC = Number(addr); }},
            0x35: { name: 'JL', execute: (addr) => { if (this.SF) this.PC = Number(addr); }},
            0x36: { name: 'JLE', execute: (addr) => { if (this.SF || this.ZF) this.PC = Number(addr); }},
            0x37: { name: 'JG', execute: (addr) => { if (!this.SF && !this.ZF) this.PC = Number(addr); }},
            0x38: { name: 'JGE', execute: (addr) => { if (!this.SF) this.PC = Number(addr); }},
            0x39: { name: 'CALL', execute: (addr) => {
                this.pushStack(BigInt(this.PC));
                this.PC = Number(addr);
            }},
            0x3A: { name: 'RET', execute: () => { this.PC = Number(this.popStack()); }},
            0x3B: { name: 'INT', execute: (num) => this.handleInterrupt(Number(num)) },
            0x3C: { name: 'HLT', execute: () => this.running = false },
            
            // 0x40-0x4F: 内存操作
            0x40: { name: 'LOAD', execute: (rd, ra) => {
                const addr = Number(this.regGet(ra));
                if (addr >= 0 && addr + 8 <= this.memorySize) {
                    const val = this.readUint64(addr);
                    this.regSet(rd, val);
                }
            }},
            0x41: { name: 'STORE', execute: (rd, ra) => {
                const addr = Number(this.regGet(rd));
                if (addr >= 0 && addr + 8 <= this.memorySize) {
                    this.writeUint64(addr, this.regGet(ra));
                }
            }},
            0x42: { name: 'LOADB', execute: (rd, ra) => {
                const addr = Number(this.regGet(ra));
                if (addr >= 0 && addr < this.memorySize) {
                    this.regSet(rd, BigInt(this.memory[addr]));
                }
            }},
            0x43: { name: 'STOREB', execute: (rd, ra) => {
                const addr = Number(this.regGet(rd));
                if (addr >= 0 && addr < this.memorySize) {
                    this.memory[addr] = Number(this.regGet(ra) & 0xFFn);
                }
            }},
            0x44: { name: 'LOADH', execute: (rd, ra) => {
                const addr = Number(this.regGet(ra));
                if (addr >= 0 && addr + 2 <= this.memorySize) {
                    this.regSet(rd, BigInt(this.readUint16(addr)));
                }
            }},
            0x45: { name: 'STOREH', execute: (rd, ra) => {
                const addr = Number(this.regGet(rd));
                if (addr >= 0 && addr + 2 <= this.memorySize) {
                    this.writeUint16(addr, Number(this.regGet(ra) & 0xFFFFn));
                }
            }},
            0x46: { name: 'PUSH', execute: (rd) => this.pushStack(this.regGet(rd)) },
            0x47: { name: 'POP', execute: (rd) => this.regSet(rd, this.popStack()) },
            0x48: { name: 'LEA', execute: (rd, addr) => this.regSet(rd, addr) },
            
            // 0x50-0x5F: 向量/SIMD指令
            0x50: { name: 'VADD', execute: (vd, va, vb) => {
                const baseD = Number(vd) * 8, baseA = Number(va) * 8, baseB = Number(vb) * 8;
                for (let i = 0; i < 8; i++) {
                    this.vectorRegisters[baseD + i] = this.vectorRegisters[baseA + i] + this.vectorRegisters[baseB + i];
                }
            }},
            0x51: { name: 'VMUL', execute: (vd, va, vb) => {
                const baseD = Number(vd) * 8, baseA = Number(va) * 8, baseB = Number(vb) * 8;
                for (let i = 0; i < 8; i++) {
                    this.vectorRegisters[baseD + i] = this.vectorRegisters[baseA + i] * this.vectorRegisters[baseB + i];
                }
            }},
            0x52: { name: 'VMIN', execute: (vd, va, vb) => {
                const baseD = Number(vd) * 8, baseA = Number(va) * 8, baseB = Number(vb) * 8;
                for (let i = 0; i < 8; i++) {
                    this.vectorRegisters[baseD + i] = Math.min(this.vectorRegisters[baseA + i], this.vectorRegisters[baseB + i]);
                }
            }},
            0x53: { name: 'VMAX', execute: (vd, va, vb) => {
                const baseD = Number(vd) * 8, baseA = Number(va) * 8, baseB = Number(vb) * 8;
                for (let i = 0; i < 8; i++) {
                    this.vectorRegisters[baseD + i] = Math.max(this.vectorRegisters[baseA + i], this.vectorRegisters[baseB + i]);
                }
            }},
            
            // 0x60-0x6F: AI/张量指令
            0x60: { name: 'MADD', execute: (rd, ra, rb) => {
                // 矩阵加法 (简化实现)
                const size = Number(ra);
                for (let i = 0; i < size * size && i < 256; i++) {
                    const offset = i * 8;
                    const aVal = this.readFloat64(Number(this.controlRegisters[0]) + offset);
                    const bVal = this.readFloat64(Number(this.controlRegisters[1]) + offset);
                    this.writeFloat64(Number(this.controlRegisters[2]) + offset, aVal + bVal);
                }
            }},
            0x61: { name: 'MMUL', execute: (rd, ra, rb) => {
                // 矩阵乘法 (简化实现)
                const size = Number(ra);
                for (let i = 0; i < size && i < 16; i++) {
                    for (let j = 0; j < size && j < 16; j++) {
                        let sum = 0;
                        for (let k = 0; k < size && k < 16; k++) {
                            const aVal = this.readFloat64(Number(this.controlRegisters[0]) + (i * size + k) * 8);
                            const bVal = this.readFloat64(Number(this.controlRegisters[1]) + (k * size + j) * 8);
                            sum += aVal * bVal;
                        }
                        this.writeFloat64(Number(this.controlRegisters[2]) + (i * size + j) * 8, sum);
                    }
                }
            }},
            0x63: { name: 'RELU', execute: (rd, ra) => {
                const baseD = Number(rd) * 8, baseA = Number(ra) * 8;
                for (let i = 0; i < 8; i++) {
                    this.vectorRegisters[baseD + i] = Math.max(0, this.vectorRegisters[baseA + i]);
                }
            }},
            
            // 0x70-0x7F: 并行/多线程
            0x70: { name: 'SPAWN', execute: (rd, addr) => {
                const threadId = this.threads.size + 1;
                this.threads.set(threadId, {
                    PC: Number(addr),
                    registers: new BigUint64Array(this.registers),
                    running: true
                });
                this.regSet(rd, BigInt(threadId));
            }},
            0x71: { name: 'JOIN', execute: (rd) => {
                const tid = Number(this.regGet(rd));
                if (this.threads.has(tid)) {
                    this.threads.get(tid).running = false;
                }
            }},
            0x72: { name: 'SYNC', execute: () => {
                // 线程同步
            }},
            0x73: { name: 'SEND', execute: (rd, ra) => {
                // 发送消息
                const tid = Number(this.regGet(rd));
                if (this.threads.has(tid)) {
                    this.threads.get(tid).message = this.regGet(ra);
                }
            }},
            0x74: { name: 'RECV', execute: (rd) => {
                // 接收消息
                if (this.currentThread && this.threads.has(this.currentThread)) {
                    this.regSet(rd, this.threads.get(this.currentThread).message || 0n);
                }
            }},
            
            // 0x80-0x8F: 系统指令
            0x80: { name: 'SYSCALL', execute: () => this.handleSyscall() },
            0x81: { name: 'READ', execute: (rd, port) => this.regSet(rd, this.readPort(Number(port))) },
            0x82: { name: 'WRITE', execute: (rd, port) => this.writePort(Number(port), this.regGet(rd)) },
            0x83: { name: 'MAPPING', execute: (rd, ra) => this.regSet(rd, this.mapMemory(Number(ra))) },
            0x84: { name: 'CACHE', execute: (op) => {
                // 缓存操作
            }},
            0x85: { name: 'MIGRATE', execute: (rd) => {
                // 线程迁移
            }},
            
            // 0x90-0x9F: 扩展指令
            0x90: { name: 'MOV', execute: (rd, ra) => this.regSet(rd, this.regGet(ra)) },
            0x91: { name: 'MOVI', execute: (rd, imm) => this.regSet(rd, imm) },
        };
    }

    // 寄存器操作
    regGet(idx) {
        return this.registers[Number(idx)] || 0n;
    }

    regSet(idx, val) {
        this.registers[Number(idx)] = val;
    }

    // 栈操作
    pushStack(val) {
        this.SP -= 8;
        if (this.SP >= 0) {
            this.writeUint64(this.SP, val);
        }
    }

    popStack() {
        const val = this.readUint64(this.SP);
        this.SP += 8;
        return val;
    }

    // 内存读写
    readUint64(addr) {
        const view = new DataView(this.memory.buffer);
        return view.getBigUint64(addr, true);
    }

    writeUint64(addr, val) {
        const view = new DataView(this.memory.buffer);
        view.setBigUint64(addr, val, true);
    }

    readUint32(addr) {
        const view = new DataView(this.memory.buffer);
        return view.getUint32(addr, true);
    }

    writeUint32(addr, val) {
        const view = new DataView(this.memory.buffer);
        view.setUint32(addr, val, true);
    }

    readUint16(addr) {
        const view = new DataView(this.memory.buffer);
        return view.getUint16(addr, true);
    }

    writeUint16(addr, val) {
        const view = new DataView(this.memory.buffer);
        view.setUint16(addr, val, true);
    }

    readFloat64(addr) {
        const view = new DataView(this.memory.buffer);
        return view.getFloat64(addr, true);
    }

    writeFloat64(addr, val) {
        const view = new DataView(this.memory.buffer);
        view.setFloat64(addr, val, true);
    }

    // 内存映射
    mapMemory(size) {
        const addr = this.HP;
        this.HP += size;
        return BigInt(addr);
    }

    // 端口读写
    readPort(port) {
        switch(port) {
            case 0: return BigInt(Date.now() & 0xFFFFFFFF);
            case 1: return BigInt(this.memorySize);
            case 2: return BigInt(this.PC);
            default: return 0n;
        }
    }

    writePort(port, val) {
        // 端口写入 (可以扩展支持外设)
    }

    // 中断处理
    handleInterrupt(num) {
        const handler = this.interrupts.get(num);
        if (handler) {
            this.pushStack(BigInt(this.PC));
            this.PC = handler;
        }
    }

    // 系统调用
    handleSyscall() {
        const syscallNum = Number(this.registers[7]); // R7通常用于系统调用号
        switch(syscallNum) {
            case 0: // exit
                this.running = false;
                break;
            case 1: // write
                const fd = Number(this.registers[0]);
                const buf = Number(this.registers[1]);
                const len = Number(this.registers[2]);
                if (fd === 1 || fd === 2) { // stdout/stderr
                    const text = new TextDecoder().decode(this.memory.slice(buf, buf + len));
                    console.log(text);
                }
                break;
            case 2: // read
                // 实现读取
                break;
            case 3: // open
                break;
            case 4: // close
                break;
            default:
                console.log(`Unknown syscall: ${syscallNum}`);
        }
    }

    // 加载程序
    loadProgram(code, offset = 0x1000) {
        for (let i = 0; i < code.length; i++) {
            this.memory[offset + i] = code[i];
        }
        this.PC = offset;
        this.SP = this.memorySize - 8;
        this.HP = this.memorySize;
    }

    // 加载UniISA汇编
    loadAssembly(asm) {
        const bytecode = this.assemble(asm);
        this.loadProgram(bytecode);
    }

    // 汇编器
    assemble(asm) {
        const lines = asm.split('\n');
        const bytecode = [];
        const labels = new Map();
        const output = [];

        // 第一遍：收集标签
        let addr = 0;
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(';')) continue;
            
            if (trimmed.endsWith(':')) {
                labels.set(trimmed.slice(0, -1), addr);
            } else {
                addr += 4; // 每条指令4字节
            }
        }

        // 第二遍：生成字节码
        addr = 0;
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(';') || trimmed.endsWith(':')) continue;

            const parts = trimmed.split(/[,\s]+/);
            const op = parts[0].toUpperCase();
            const args = parts.slice(1).map(a => a.trim());

            const instr = this.parseInstruction(op, args, labels);
            if (instr) {
                output.push(...instr);
                addr += 4;
            }
        }

        return new Uint8Array(output);
    }

    parseInstruction(op, args, labels) {
        const getOperand = (arg) => {
            if (!arg) return 0n;
            if (arg.startsWith('R') || arg.startsWith('r')) {
                return BigInt(parseInt(arg.slice(1)));
            }
            if (arg.startsWith('V') || arg.startsWith('v')) {
                return BigInt(parseInt(arg.slice(1)) + 64); // 向量寄存器偏移
            }
            if (arg.startsWith('0x')) {
                return BigInt(parseInt(arg, 16));
            }
            if (!isNaN(parseInt(arg))) {
                return BigInt(parseInt(arg));
            }
            if (labels.has(arg)) {
                return BigInt(labels.get(arg));
            }
            return 0n;
        };

        const instructions = {
            'NOP': [0x00, 0, 0, 0],
            'ADD': [0x01, getOperand(args[0]), getOperand(args[1]), getOperand(args[2])],
            'SUB': [0x02, getOperand(args[0]), getOperand(args[1]), getOperand(args[2])],
            'MUL': [0x03, getOperand(args[0]), getOperand(args[1]), getOperand(args[2])],
            'DIV': [0x04, getOperand(args[0]), getOperand(args[1]), getOperand(args[2])],
            'MOV': [0x90, getOperand(args[0]), getOperand(args[1]), 0],
            'MOVI': [0x91, getOperand(args[0]), getOperand(args[1]), 0],
            'LOAD': [0x40, getOperand(args[0]), getOperand(args[1]), 0],
            'STORE': [0x41, getOperand(args[0]), getOperand(args[1]), 0],
            'JMP': [0x30, getOperand(args[0]), 0, 0],
            'JZ': [0x31, getOperand(args[0]), 0, 0],
            'CALL': [0x39, getOperand(args[0]), 0, 0],
            'RET': [0x3A, 0, 0, 0],
            'HALT': [0x3C, 0, 0, 0],
            'PUSH': [0x46, getOperand(args[0]), 0, 0],
            'POP': [0x47, getOperand(args[0]), 0, 0],
            'CMP': [0x20, getOperand(args[0]), getOperand(args[1]), 0],
            'AND': [0x10, getOperand(args[0]), getOperand(args[1]), getOperand(args[2]) || 0n],
            'OR': [0x11, getOperand(args[0]), getOperand(args[1]), getOperand(args[2]) || 0n],
            'XOR': [0x12, getOperand(args[0]), getOperand(args[1]), getOperand(args[2]) || 0n],
            'SYSCALL': [0x80, 0, 0, 0],
        };

        const instr = instructions[op];
        if (!instr) {
            console.warn(`Unknown instruction: ${op}`);
            return null;
        }

        return instr;
    }

    // 执行单条指令
    executeInstruction() {
        if (this.PC >= this.memorySize || this.PC < 0) {
            this.running = false;
            return;
        }

        const opcode = this.memory[this.PC];
        const rd = this.memory[this.PC + 1];
        const ra = this.memory[this.PC + 2];
        const rb = this.memory[this.PC + 3];

        const instr = this.instructions[opcode];
        if (instr) {
            try {
                const imm = this.readUint32(this.PC + 4);
                instr.execute(
                    BigInt(rd),
                    BigInt(ra),
                    BigInt(rb),
                    BigInt(imm)
                );
            } catch (e) {
                console.error(`Error executing ${instr.name}:`, e);
            }
        }

        if (opcode !== 0x30 && opcode !== 0x31 && opcode !== 0x32 && 
            opcode !== 0x33 && opcode !== 0x34 && opcode !== 0x35 && 
            opcode !== 0x36 && opcode !== 0x37 && opcode !== 0x38 && 
            opcode !== 0x39) {
            this.PC += 4;
        }

        this.stats.instructions++;
        this.stats.cycles += 10;
    }

    // 运行程序
    run(maxCycles = 1000000) {
        this.running = true;
        let cycles = 0;

        while (this.running && cycles < maxCycles) {
            this.executeInstruction();
            cycles++;
        }

        return {
            success: !this.running,
            cycles,
            stats: { ...this.stats }
        };
    }

    // 状态快照
    snapshot() {
        return {
            registers: Array.from(this.registers),
            PC: this.PC,
            SP: this.SP,
            flags: { ZF: this.ZF, CF: this.CF, OF: this.OF, SF: this.SF }
        };
    }

    // 恢复状态
    restore(snapshot) {
        this.registers = new BigUint64Array(snapshot.registers);
        this.PC = snapshot.PC;
        this.SP = snapshot.SP;
        this.ZF = snapshot.flags.ZF;
        this.CF = snapshot.flags.CF;
        this.OF = snapshot.flags.OF;
        this.SF = snapshot.flags.SF;
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UniversalVM };
}

if (typeof window !== 'undefined') {
    window.UniversalVM = UniversalVM;
}
