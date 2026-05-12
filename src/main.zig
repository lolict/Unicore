const std = @import("std");
const uniisa = @import("core/uniisa.zig");

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    const stdout = std.io.getStdOut().writer();

    try stdout.print(
        \\========================================
        \\ UniCore - Universal Core Platform
        \\========================================
        \\
    , .{});

    var vm = try uniisa.VM.init(allocator);
    defer vm.deinit();

    const program = [_]uniisa.Instruction{
        uniisa.Instruction.encode(.MOVI, 1, 0, 0, 5),
        uniisa.Instruction.encode(.MOVI, 2, 0, 0, 3),
        uniisa.Instruction.encode(.ADD, 3, 1, 2, 0),
        uniisa.Instruction.encode(.SUB, 4, 1, 2, 0),
        uniisa.Instruction.encode(.MUL, 5, 3, 4, 0),
        uniisa.Instruction.encode(.HALT, 0, 0, 0, 0),
    };

    vm.loadProgram(&program, 0x1000);
    const count = vm.run(1000);

    try stdout.print(
        \\✅ 测试程序执行完成
        \\  指令数: {}
        \\
        \\  寄存器状态:
        \\  R0={}
        \\  R1={}
        \\  R2={}
        \\  R3={}
        \\  R4={}
        \\  R5={}
        \\
    , .{
        count,
        vm.regs.general[0],
        vm.regs.general[1],
        vm.regs.general[2],
        vm.regs.general[3],
        vm.regs.general[4],
        vm.regs.general[5],
    });

    try stdout.print("🎉 UniCore 极简核心框架初始化成功！\n", .{});
}
