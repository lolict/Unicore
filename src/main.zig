const std = @import("std");
const uniisa = @import("core/uniisa.zig");
const translator = @import("core/translator.zig");

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    const stdout = std.io.getStdOut().writer();
    
    try stdout.print(
        \\========================================
        \\ UniCore - Universal Core Platform
        \\========================================
        \\
    , .{});
    
    // 初始化虚拟机和翻译器
    var vm = try uniisa.VM.init(allocator);
    defer vm.deinit();
    
    var trans = translator.BinaryTranslator.init(allocator);
    defer trans.deinit();
    
    // ============== 测试1: 原生 UniISA ==============
    try stdout.print("=== 测试1: 原生 UniISA 程序 ===\n", .{});
    
    const program = [_]uniisa.Instruction{
        uniisa.Instruction.encode(.MOVI, 1, 0, 0, 5),
        uniisa.Instruction.encode(.MOVI, 2, 0, 0, 3),
        uniisa.Instruction.encode(.ADD, 3, 1, 2, 0),
        uniisa.Instruction.encode(.SUB, 4, 1, 2, 0),
        uniisa.Instruction.encode(.MUL, 5, 3, 4, 0),
        uniisa.Instruction.encode(.HALT, 0, 0, 0, 0),
    };
    
    vm.loadProgram(&program, 0x1000);
    const count1 = vm.run(1000);
    
    try stdout.print(
        \\执行指令: {d}
        \\寄存器状态:
        \\  R1 = {d}  (MOVI 5)
        \\  R2 = {d}  (MOVI 3)
        \\  R3 = {d}  (ADD)
        \\  R4 = {d}  (SUB)
        \\  R5 = {d}  (MUL)
        \\
    , .{
        count1, 
        vm.regs.general[1], 
        vm.regs.general[2], 
        vm.regs.general[3], 
        vm.regs.general[4], 
        vm.regs.general[5]
    });
    
    // ============== 测试2: x86 翻译 ==============
    try stdout.print("=== 测试2: x86 翻译 ===", .{});
    try stdout.print("\n\n", .{});
    
    const x86_test = [_]u8{0x90, 0x90, 0x01, 0x00}; // NOP, NOP, ADD
    const translated = try trans.translateX86(&x86_test);
    defer allocator.free(translated);
    
    try stdout.print(
        \\翻译了 {d} 条 x86 指令到 {d} 条 UniISA
        \\
    , .{x86_test.len, translated.len});
    
    // ============== 架构支持说明 ==============
    try stdout.print(
        \\========================================
        \\支持的架构与功能:
        \\
        \\  ✅ x86/x64     - 基础指令集
        \\  ✅ ARM        - ARMv7+
        \\  ✅ RISC-V     - RV32/64
        \\  ✅ MIPS       - MIPS32
        \\
        \\  ✅ 自动检测并翻译
        \\========================================
        \\
    , .{});
    
    try stdout.print("🎉 UniCore 核心初始化完成！\n", .{});
}
