const std = @import("std");
const uniisa = @import("uniisa.zig");

/// 二进制翻译器 - 多种架构到 UniISA
pub const BinaryTranslator = struct {
    allocator: std.mem.Allocator,
    
    const Self = @This();
    
    pub fn init(allocator: std.mem.Allocator) Self {
        return .{ .allocator = allocator };
    }
    
    pub fn deinit(self: *Self) void {
        _ = self;
    }
    
    // ========== 翻译: x86/x64 → UniISA ==========
    pub fn translateX86(self: *Self, x86_bytes: []const u8) ![]uniisa.Instruction {
        _ = self;
        var program = std.ArrayList(uniisa.Instruction).init(self.allocator);
        defer program.deinit();
        
        var i: usize = 0;
        while (i < x86_bytes.len) {
            const byte = x86_bytes[i];
            
            switch (byte) {
                0x90 => { // NOP
                    try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
                    i += 1;
                },
                0x01 => { // ADD r/m32, r32
                    try program.append(uniisa.Instruction.encode(.ADD, 0, 0, 0, 0));
                    i += 1;
                },
                0x29 => { // SUB r/m32, r32
                    try program.append(uniisa.Instruction.encode(.SUB, 0, 0, 0, 0));
                    i += 1;
                },
                0x21 => { // AND r/m32, r32
                    try program.append(uniisa.Instruction.encode(.AND, 0, 0, 0, 0));
                    i += 1;
                },
                0x09 => { // OR r/m32, r32
                    try program.append(uniisa.Instruction.encode(.OR, 0, 0, 0, 0));
                    i += 1;
                },
                0x31 => { // XOR r/m32, r32
                    try program.append(uniisa.Instruction.encode(.XOR, 0, 0, 0, 0));
                    i += 1;
                },
                0xC3 => { // RET
                    try program.append(uniisa.Instruction.encode(.RET, 0, 0, 0, 0));
                    i += 1;
                },
                0xC9 => { // LEAVE
                    try program.append(uniisa.Instruction.encode(.POP, 0, 0, 0, 0));
                    i += 1;
                },
                0xB8 => { // MOV EAX, imm32
                    try program.append(uniisa.Instruction.encode(.MOVI, 0, 0, 0, 0));
                    i += 5;
                },
                0xEB => { // JMP rel8
                    try program.append(uniisa.Instruction.encode(.JMP, 0, 0, 0, x86_bytes[i+1]));
                    i += 2;
                },
                else => { // 未知指令转 NOP
                    try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
                    i += 1;
                }
            }
        }
        
        return program.toOwnedSlice();
    }
    
    // ========== 翻译: ARM → UniISA ==========
    pub fn translateARM(self: *Self, arm_bytes: []const u8) ![]uniisa.Instruction {
        _ = self;
        var program = std.ArrayList(uniisa.Instruction).init(self.allocator);
        defer program.deinit();
        
        var i: usize = 0;
        while (i < arm_bytes.len - 3) : (i += 4) {
            const instr = @as(u32, @bitCast(arm_bytes[i..i+4][0..4].*));
            
            if ((instr & 0xFFF00000) == 0xE3200000) { // NOP
                try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
            } else if ((instr & 0xFF000000) == 0xE0800000) { // ADD
                const rd: u6 = @intCast((instr >> 12) & 0xF);
                const rn: u6 = @intCast((instr >> 16) & 0xF);
                const rm: u6 = @intCast(instr & 0xF);
                try program.append(uniisa.Instruction.encode(.ADD, rd, rn, rm, 0));
            } else if ((instr & 0xFF000000) == 0xE0400000) { // SUB
                const rd: u6 = @intCast((instr >> 12) & 0xF);
                const rn: u6 = @intCast((instr >> 16) & 0xF);
                const rm: u6 = @intCast(instr & 0xF);
                try program.append(uniisa.Instruction.encode(.SUB, rd, rn, rm, 0));
            } else if ((instr & 0xFF000000) == 0xE0000000) { // AND
                const rd: u6 = @intCast((instr >> 12) & 0xF);
                const rn: u6 = @intCast((instr >> 16) & 0xF);
                const rm: u6 = @intCast(instr & 0xF);
                try program.append(uniisa.Instruction.encode(.AND, rd, rn, rm, 0));
            } else if ((instr & 0xFF000000) == 0xE1800000) { // ORR
                const rd: u6 = @intCast((instr >> 12) & 0xF);
                const rn: u6 = @intCast((instr >> 16) & 0xF);
                const rm: u6 = @intCast(instr & 0xF);
                try program.append(uniisa.Instruction.encode(.OR, rd, rn, rm, 0));
            } else if ((instr & 0xFF000000) == 0xE1A00000) { // MOV
                const rd: u6 = @intCast((instr >> 12) & 0xF);
                const rm: u6 = @intCast(instr & 0xF);
                try program.append(uniisa.Instruction.encode(.MOV, rd, rm, 0, 0));
            } else if ((instr & 0xFFE00000) == 0xE1A0F000) { // RET
                try program.append(uniisa.Instruction.encode(.RET, 0, 0, 0, 0));
            } else { // 未知指令
                try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
            }
        }
        
        return program.toOwnedSlice();
    }
    
    // ========== 翻译: RISC-V → UniISA ==========
    pub fn translateRISC_V(self: *Self, riscv_bytes: []const u8) ![]uniisa.Instruction {
        _ = self;
        var program = std.ArrayList(uniisa.Instruction).init(self.allocator);
        defer program.deinit();
        
        var i: usize = 0;
        while (i < riscv_bytes.len - 3) : (i += 4) {
            const instr = @as(u32, @bitCast(riscv_bytes[i..i+4][0..4].*));
            const opcode = instr & 0x7F;
            const rd: u6 = @intCast((instr >> 7) & 0x1F);
            const rs1: u6 = @intCast((instr >> 15) & 0x1F);
            const rs2: u6 = @intCast((instr >> 20) & 0x1F);
            const funct3: u6 = @intCast((instr >> 12) & 0x7);
            
            if (opcode == 0x13) { // OP-IMM (I-type)
                switch (funct3) {
                    0x0 => { // ADDI
                        const imm = @intCast(u6, (instr >> 20) & 0x3F);
                        try program.append(uniisa.Instruction.encode(.ADD, rd, rs1, 0, imm));
                    },
                    0x7 => { // ANDI
                        const imm = @intCast(u6, (instr >> 20) & 0x3F);
                        try program.append(uniisa.Instruction.encode(.AND, rd, rs1, 0, imm));
                    },
                    0x6 => { // ORI
                        const imm = @intCast(u6, (instr >> 20) & 0x3F);
                        try program.append(uniisa.Instruction.encode(.OR, rd, rs1, 0, imm));
                    },
                    else => {
                        try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
                    }
                }
            } else if (opcode == 0x33) { // OP (R-type)
                switch (funct3) {
                    0x0 => {
                        const bit7 = (instr >> 30) & 1;
                        if (bit7 == 1) { // SUB
                            try program.append(uniisa.Instruction.encode(.SUB, rd, rs1, rs2, 0));
                        } else { // ADD
                            try program.append(uniisa.Instruction.encode(.ADD, rd, rs1, rs2, 0));
                        }
                    },
                    0x4 => { // XOR
                        try program.append(uniisa.Instruction.encode(.XOR, rd, rs1, rs2, 0));
                    },
                    0x6 => { // OR
                        try program.append(uniisa.Instruction.encode(.OR, rd, rs1, rs2, 0));
                    },
                    0x7 => { // AND
                        try program.append(uniisa.Instruction.encode(.AND, rd, rs1, rs2, 0));
                    },
                    else => {
                        try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
                    }
                }
            } else if (opcode == 0x6F) { // JAL
                const imm = @intCast(u6, (instr >> 21) & 0x3F);
                try program.append(uniisa.Instruction.encode(.JMP, rd, 0, 0, imm));
            } else if (opcode == 0x67) { // JALR
                const imm = @intCast(u6, (instr >> 20) & 0x3F);
                try program.append(uniisa.Instruction.encode(.CALL, rd, rs1, 0, imm));
            } else {
                try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
            }
        }
        
        return program.toOwnedSlice();
    }
    
    // ========== 翻译: MIPS → UniISA ==========
    pub fn translateMIPS(self: *Self, mips_bytes: []const u8) ![]uniisa.Instruction {
        _ = self;
        var program = std.ArrayList(uniisa.Instruction).init(self.allocator);
        defer program.deinit();
        
        var i: usize = 0;
        while (i < mips_bytes.len - 3) : (i += 4) {
            const instr = @as(u32, @bitCast(mips_bytes[i..i+4][0..4].*));
            const op: u6 = @intCast((instr >> 26) & 0x3F);
            const rs: u6 = @intCast((instr >> 21) & 0x1F);
            const rt: u6 = @intCast((instr >> 16) & 0x1F);
            const rd: u6 = @intCast((instr >> 11) & 0x1F);
            const funct: u6 = @intCast(instr & 0x3F);
            
            if (op == 0) { // SPECIAL
                switch (funct) {
                    0x20 => { // ADD
                        try program.append(uniisa.Instruction.encode(.ADD, rd, rs, rt, 0));
                    },
                    0x22 => { // SUB
                        try program.append(uniisa.Instruction.encode(.SUB, rd, rs, rt, 0));
                    },
                    0x24 => { // AND
                        try program.append(uniisa.Instruction.encode(.AND, rd, rs, rt, 0));
                    },
                    0x25 => { // OR
                        try program.append(uniisa.Instruction.encode(.OR, rd, rs, rt, 0));
                    },
                    0x26 => { // XOR
                        try program.append(uniisa.Instruction.encode(.XOR, rd, rs, rt, 0));
                    },
                    0x0C => { // SYSCALL
                        try program.append(uniisa.Instruction.encode(.SYSCALL, 0, 0, 0, 0));
                    },
                    else => {
                        try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
                    }
                }
            } else if (op == 0x08) { // ADDI
                const imm = @intCast(u6, instr & 0x3F);
                try program.append(uniisa.Instruction.encode(.ADD, rt, rs, 0, imm));
            } else if (op == 0x0C) { // ANDI
                const imm = @intCast(u6, instr & 0x3F);
                try program.append(uniisa.Instruction.encode(.AND, rt, rs, 0, imm));
            } else if (op == 0x0D) { // ORI
                const imm = @intCast(u6, instr & 0x3F);
                try program.append(uniisa.Instruction.encode(.OR, rt, rs, 0, imm));
            } else if (op == 0x02) { // J
                const addr = @intCast(u6, instr & 0x3F);
                try program.append(uniisa.Instruction.encode(.JMP, 0, 0, 0, addr));
            } else if (op == 0x03) { // JAL
                const addr = @intCast(u6, instr & 0x3F);
                try program.append(uniisa.Instruction.encode(.CALL, rd, 0, 0, addr));
            } else {
                try program.append(uniisa.Instruction.encode(.NOP, 0, 0, 0, 0));
            }
        }
        
        return program.toOwnedSlice();
    }
    
    // ========== 自动检测并翻译 ==========
    pub fn translateAuto(self: *Self, binary_data: []const u8) ![]uniisa.Instruction {
        if (binary_data.len >= 4) {
            const word = @as(u32, @bitCast(binary_data[0..4].*));
            if ((word & 0xFF000000) == 0xE3200000 or (word & 0xFF000000) == 0xE1A00000) {
                return self.translateARM(binary_data);
            }
            const opcode = word & 0x7F;
            if (opcode == 0x13 or opcode == 0x33 or opcode == 0x6F or opcode == 0x67) {
                return self.translateRISC_V(binary_data);
            }
        }
        return self.translateX86(binary_data);
    }
};
