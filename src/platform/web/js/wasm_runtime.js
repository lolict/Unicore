/**
 * UniCore WASM/WASI 统一运行时
 * 适配所有平台的统一执行环境
 */

class UniCoreRuntime {
    constructor() {
        this.memory = null;
        this.registers = new Uint64Array(32);
        this.pc = 0;
        this.sp = 0;
        this.running = false;
        this.modules = new Map();
        this.exports = new Map();
    }

    // 加载WASM模块
    async load(wasmBytes) {
        const importObject = {
            env: {
                memory: new WebAssembly.Memory({ initial: 256, maximum: 512 }),
                print: (ptr) => this.print(ptr),
                alloc: (size) => this.alloc(size),
                free: (ptr) => this.free(ptr),
            },
            wasi_snapshot_preview1: {
                fd_write: (fd, iovs_ptr, iovs_len, nwritten_ptr) => this.fd_write(fd, iovs_ptr, iovs_len, nwritten_ptr),
                fd_read: (fd, iovs_ptr, iovs_len, nread_ptr) => this.fd_read(fd, iovs_ptr, iovs_len, nread_ptr),
                proc_exit: (code) => this.proc_exit(code),
            }
        };

        try {
            const result = await WebAssembly.instantiate(wasmBytes, importObject);
            this.memory = importObject.env.memory;
            return result.instance;
        } catch (error) {
            console.error('Failed to load WASM:', error);
            throw error;
        }
    }

    // 初始化
    init(memorySize = 16 * 1024 * 1024) {
        this.memory = new WebAssembly.Memory({ initial: memorySize / 65536 });
        this.registers.fill(0);
        this.pc = 0;
        this.sp = memorySize;
        this.running = true;
    }

    // 分配内存
    alloc(size) {
        const view = new Uint8Array(this.memory.buffer);
        const ptr = Math.floor(Math.random() * (this.memory.buffer.byteLength - size));
        return ptr;
    }

    // 释放内存
    free(ptr) {
        // 简化实现
    }

    // 执行指令
    execute_instruction(opcode, operands) {
        switch (opcode) {
            case 0x00: // NOP
                break;
            case 0x01: // ADD
                this.registers[operands[2]] = this.registers[operands[0]] + this.registers[operands[1]];
                break;
            case 0x02: // SUB
                this.registers[operands[2]] = this.registers[operands[0]] - this.registers[operands[1]];
                break;
            case 0x03: // MUL
                this.registers[operands[2]] = this.registers[operands[0]] * this.registers[operands[1]];
                break;
            case 0x04: // DIV
                if (this.registers[operands[1]] !== 0) {
                    this.registers[operands[2]] = Math.floor(this.registers[operands[0]] / this.registers[operands[1]]);
                }
                break;
            case 0x30: // JMP
                this.pc = this.registers[operands[0]];
                break;
            case 0x33: // HALT
                this.running = false;
                break;
            default:
                console.warn(`Unknown opcode: ${opcode}`);
        }
    }

    // 打印
    print(ptr) {
        const view = new Uint8Array(this.memory.buffer);
        let end = ptr;
        while (view[end] !== 0) end++;
        const bytes = view.slice(ptr, end);
        const text = new TextDecoder().decode(bytes);
        console.log(text);
    }

    // WASI 实现
    fd_write(fd, iovs_ptr, iovs_len, nwritten_ptr) {
        const view = new Uint32Array(this.memory.buffer);
        let total = 0;
        for (let i = 0; i < iovs_len; i++) {
            const ptr = view[iovs_ptr / 4 + i * 2];
            const len = view[iovs_ptr / 4 + i * 2 + 1];
            total += len;
        }
        view[nwritten_ptr / 4] = total;
        return 0;
    }

    fd_read(fd, iovs_ptr, iovs_len, nread_ptr) {
        return 0;
    }

    proc_exit(code) {
        console.log(`Process exited with code: ${code}`);
        this.running = false;
    }

    // 运行主循环
    async run(instance) {
        this.running = true;
        while (this.running) {
            try {
                if (instance.exports && instance.exports._start) {
                    await instance.exports._start();
                }
                break;
            } catch (error) {
                console.error('Runtime error:', error);
                break;
            }
        }
    }
}

// WASM编译辅助
class WASMCompiler {
    static compileISA(ir) {
        const bytecode = [];
        for (const instr of ir) {
            bytecode.push(instr.opcode);
            if (instr.operands) {
                for (const op of instr.operands) {
                    if (typeof op === 'number') {
                        bytecode.push(...new Uint8Array(new BigUint64Array([BigInt(op)]).buffer));
                    }
                }
            }
        }
        return new Uint8Array(bytecode);
    }

    static disassemble(wasmBytes) {
        const instructions = [];
        let i = 0;
        while (i < wasmBytes.length) {
            const opcode = wasmBytes[i];
            instructions.push({
                offset: i,
                opcode: opcode,
                name: this.opcodeName(opcode)
            });
            i++;
        }
        return instructions;
    }

    static opcodeName(opcode) {
        const names = {
            0x00: 'NOP', 0x01: 'ADD', 0x02: 'SUB', 0x03: 'MUL', 0x04: 'DIV',
            0x30: 'JMP', 0x33: 'HALT', 0x40: 'LOAD', 0x41: 'STORE'
        };
        return names[opcode] || `UNKNOWN(${opcode})`;
    }
}

// 平台适配器
class PlatformAdapter {
    constructor(platform) {
        this.platform = platform;
        this.capabilities = this.detectCapabilities();
    }

    detectCapabilities() {
        if (typeof window !== 'undefined') {
            return { browser: true, webgl: !!window.WebGLRenderingContext };
        }
        if (typeof process !== 'undefined') {
            return { nodejs: true };
        }
        return { unknown: true };
    }

    getRuntime() {
        if (this.capabilities.browser) {
            return new UniCoreRuntime();
        }
        // 可以扩展其他平台
        return new UniCoreRuntime();
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UniCoreRuntime, WASMCompiler, PlatformAdapter };
}

// 使用示例
async function main() {
    const runtime = new UniCoreRuntime();
    runtime.init();
    
    console.log('UniCore WASM Runtime initialized');
    console.log('Platform:', PlatformAdapter ? 'Available' : 'N/A');
    
    return runtime;
}

if (typeof window !== 'undefined') {
    window.UniCoreRuntime = UniCoreRuntime;
    window.WASMCompiler = WASMCompiler;
    window.PlatformAdapter = PlatformAdapter;
}
