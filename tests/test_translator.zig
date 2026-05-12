const std = @import("std");
const translator = @import("../src/core/translator.zig");
const uniisa = @import("../src/core/uniisa.zig");

test "x86 翻译测试" {
    const allocator = std.testing.allocator;
    var trans = translator.BinaryTranslator.init(allocator);
    defer trans.deinit();
    
    const x86_bytes = [_]u8{0x90, 0x01, 0x29, 0xC3}; // NOP, ADD, SUB, RET
    const result = try trans.translateX86(&x86_bytes);
    defer allocator.free(result);
    
    try std.testing.expect(result.len > 0);
}

test "ARM 翻译测试" {
    const allocator = std.testing.allocator;
    var trans = translator.BinaryTranslator.init(allocator);
    defer trans.deinit();
    
    const arm_bytes = [_]u8{
        0x00, 0x00, 0x20, 0xE3, // NOP
        0x00, 0x00, 0x80, 0xE0, // ADD
    };
    const result = try trans.translateARM(&arm_bytes);
    defer allocator.free(result);
    
    try std.testing.expect(result.len > 0);
}

test "RISC-V 翻译测试" {
    const allocator = std.testing.allocator;
    var trans = translator.BinaryTranslator.init(allocator);
    defer trans.deinit();
    
    const riscv_bytes = [_]u8{
        0x93, 0x00, 0x50, 0x00, // ADDI
    };
    const result = try trans.translateRISC_V(&riscv_bytes);
    defer allocator.free(result);
    
    try std.testing.expect(result.len > 0);
}

test "虚拟机执行测试" {
    const allocator = std.testing.allocator;
    var vm = try uniisa.VM.init(allocator);
    defer vm.deinit();
    
    const program = [_]uniisa.Instruction{
        uniisa.Instruction.encode(.MOVI, 1, 0, 0, 10),
        uniisa.Instruction.encode(.MOVI, 2, 0, 0, 20),
        uniisa.Instruction.encode(.ADD, 3, 1, 2, 0),
        uniisa.Instruction.encode(.HALT, 0, 0, 0, 0),
    };
    
    vm.loadProgram(&program, 0x1000);
    const count = vm.run(1000);
    
    try std.testing.expect(count == 4);
    try std.testing.expect(vm.regs.general[1] == 10);
    try std.testing.expect(vm.regs.general[2] == 20);
    try std.testing.expect(vm.regs.general[3] == 30);
}
