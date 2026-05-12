const std = @import("std");

pub const Opcode = enum(u8) {
    NOP = 0x00,
    ADD = 0x01,
    SUB = 0x02,
    MUL = 0x03,
    DIV = 0x04,
    AND = 0x05,
    OR = 0x06,
    XOR = 0x07,
    MOV = 0x08,
    MOVI = 0x09,
    LOAD = 0x0A,
    STORE = 0x0B,
    JMP = 0x0C,
    JE = 0x0D,
    JNE = 0x0E,
    CALL = 0x0F,
    RET = 0x10,
    PUSH = 0x11,
    POP = 0x12,
    CMP = 0x13,
    SYSCALL = 0xFE,
    HALT = 0xFF,
    _,
};

pub const Instruction = packed struct {
    op: Opcode,
    rd: u6 = 0,
    rs: u6 = 0,
    rt: u6 = 0,
    imm: u6 = 0,

    pub fn encode(op: Opcode, rd: u6, rs: u6, rt: u6, imm: u6) Instruction {
        return .{
            .op = op,
            .rd = rd,
            .rs = rs,
            .rt = rt,
            .imm = imm,
        };
    }
};

pub const RegisterFile = struct {
    general: [64]u64 = [_]u64{0} ** 64,
    pc: u64 = 0,
    sp: u64 = 0,
    flags: u64 = 0,

    pub fn get(self: *const RegisterFile, idx: u6) u64 {
        return self.general[idx];
    }

    pub fn set(self: *RegisterFile, idx: u6, val: u64) void {
        if (idx != 0) {
            self.general[idx] = val;
        }
    }
};

pub const Memory = struct {
    data: []u8,

    pub fn init(allocator: std.mem.Allocator, size: usize) !Memory {
        const data = try allocator.alloc(u8, size);
        std.mem.set(u8, data, 0);
        return .{ .data = data };
    }

    pub fn deinit(self: *Memory, allocator: std.mem.Allocator) void {
        allocator.free(self.data);
    }

    pub fn read(self: *const Memory, addr: u64, comptime T: type) T {
        const offset = @intCast(usize, addr);
        return std.mem.readIntNative(T, self.data[offset .. offset + @sizeOf(T)]);
    }

    pub fn write(self: *Memory, addr: u64, val: anytype) void {
        const T = @TypeOf(val);
        const offset = @intCast(usize, addr);
        std.mem.writeIntNative(T, self.data[offset .. offset + @sizeOf(T)], val);
    }
};

pub const VM = struct {
    regs: RegisterFile,
    mem: Memory,
    allocator: std.mem.Allocator,
    halted: bool = false,

    const MEM_SIZE = 16 * 1024 * 1024;

    pub fn init(allocator: std.mem.Allocator) !VM {
        return .{
            .regs = .{},
            .mem = try Memory.init(allocator, MEM_SIZE),
            .allocator = allocator,
        };
    }

    pub fn deinit(self: *VM) void {
        self.mem.deinit(self.allocator);
    }

    pub fn loadProgram(self: *VM, program: []const Instruction, base_addr: u64) void {
        var offset: usize = 0;
        var addr = base_addr;
        while (offset < program.len) : ({
            offset += 1;
            addr += @sizeOf(Instruction);
        }) {
            const inst = program[offset];
            self.mem.write(addr, @bitCast(u32, inst));
        }
        self.regs.pc = base_addr;
    }

    pub fn step(self: *VM) !bool {
        if (self.halted) return false;

        const inst_pc = self.regs.pc;
        const raw_inst = self.mem.read(inst_pc, u32);
        const inst = @bitCast(Instruction, raw_inst);

        self.regs.pc += @sizeOf(Instruction);

        switch (inst.op) {
            Opcode.NOP => {},
            Opcode.ADD => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a + b);
            },
            Opcode.SUB => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a - b);
            },
            Opcode.MUL => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a * b);
            },
            Opcode.DIV => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                if (b != 0) {
                    self.regs.set(inst.rd, a / b);
                }
            },
            Opcode.AND => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a & b);
            },
            Opcode.OR => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a | b);
            },
            Opcode.XOR => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                self.regs.set(inst.rd, a ^ b);
            },
            Opcode.MOV => {
                const val = self.regs.get(inst.rs);
                self.regs.set(inst.rd, val);
            },
            Opcode.MOVI => {
                self.regs.set(inst.rd, inst.imm);
            },
            Opcode.LOAD => {
                const addr = self.regs.get(inst.rs) + inst.imm;
                const val = self.mem.read(addr, u64);
                self.regs.set(inst.rd, val);
            },
            Opcode.STORE => {
                const addr = self.regs.get(inst.rd) + inst.imm;
                const val = self.regs.get(inst.rs);
                self.mem.write(addr, val);
            },
            Opcode.JMP => {
                self.regs.pc = inst.imm * 4;
            },
            Opcode.JE => {
                if (self.regs.flags == 0) {
                    self.regs.pc = inst.imm * 4;
                }
            },
            Opcode.JNE => {
                if (self.regs.flags != 0) {
                    self.regs.pc = inst.imm * 4;
                }
            },
            Opcode.CALL => {
                self.regs.set(63, self.regs.pc);
                self.regs.pc = inst.imm * 4;
            },
            Opcode.RET => {
                self.regs.pc = self.regs.get(63);
            },
            Opcode.PUSH => {
                self.regs.sp -= 8;
                const val = self.regs.get(inst.rd);
                self.mem.write(self.regs.sp, val);
            },
            Opcode.POP => {
                const val = self.mem.read(self.regs.sp, u64);
                self.regs.set(inst.rd, val);
                self.regs.sp += 8;
            },
            Opcode.CMP => {
                const a = self.regs.get(inst.rs);
                const b = self.regs.get(inst.rt);
                const diff = @as(i64, @intCast(a)) - @as(i64, @intCast(b));
                self.regs.flags = if (diff == 0) 0 else if (diff < 0) 1 else 2;
            },
            Opcode.HALT => {
                self.halted = true;
            },
            Opcode.SYSCALL => {
                // TODO: System calls
            },
            else => {},
        }

        return !self.halted;
    }

    pub fn run(self: *VM, max_instructions: u64) u64 {
        var count: u64 = 0;
        while (!self.halted and count < max_instructions) : (count += 1) {
            self.step() catch break;
        }
        return count;
    }
};
