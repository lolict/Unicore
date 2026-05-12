# UniCore - 通用核心平台

完全自主设计的统一指令集架构，支持多语言协作开发。

## ✨ 特性

- **UniISA**: 自主统一指令集架构
- **通用虚拟机**: 跨平台执行
- **二进制翻译器**: x86/ARM/RISC-V/MIPS 到 UniISA
- **多语言协作**: Zig + Rust + Go + Python
- **云端同步**: GitHub Gist + WebDAV + P2P
- **跨平台**: Web/Android/ESP32

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/lolict/Unicore.git
cd UniCore

# 构建
zig build

# 运行
zig build run
```

## 📁 项目结构

```
UniCore/
├── src/
│   ├── core/
│   │   ├── uniisa.zig        # UniISA 核心
│   │   ├── translator.zig    # 二进制翻译器
│   │   └── vm/               # 虚拟机
│   ├── cloud/               # 云端同步模块
│   │   ├── gist/            # GitHub Gist
│   │   ├── webdav/          # WebDAV/坚果云
│   │   ├── p2p/             # WebRTC P2P
│   │   └── sync/            # 统一调度器
│   ├── lang/               # 多语言模块
│   └── platform/           # 跨平台支持
└── tests/                  # 测试用例
```

## 🔧 二进制翻译器使用

```zig
const translator = @import("core/translator.zig");

var trans = translator.BinaryTranslator.init(allocator);
defer trans.deinit();

// 自动检测并翻译
const translated = try trans.translateAuto(binary_data);

// 或者指定架构
const x86 = try trans.translateX86(x86_bytes);
const arm = try trans.translateARM(arm_bytes);
const rv = try trans.translateRISC_V(riscv_bytes);
```

## 📡 云端同步

```python
from src.cloud.sync.scheduler import UniCoreSyncManager

# 初始化
sync = UniCoreSyncManager()
sync.configure_github("ghp_token", "username")
sync.configure_nutstore("email", "password")

# 同步数据
gist_id = sync.sync("config", data)
```

## 📋 支持的架构

- ✅ x86/x64
- ✅ ARMv7+
- ✅ RISC-V (RV32/64)
- ✅ MIPS
- ✅ WebAssembly (WASM)

## 📝 许可证

MIT
