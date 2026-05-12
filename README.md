# UniCore - 统一智能核心系统

## 愿景

> "创造一个没有平台之别、没有硬件束缚的统一计算系统"

## 核心理念

- **统一时序**: 所有操作在同一时间维度完成
- **统一能力**: 一个核心拥有所有功能
- **统一关系**: 所有平台共享同一运行时
- **无依赖**: 不依赖任何特定环境

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 智能层 (Python)                        │
│               意图理解 / 任务分解 / 知识推理                  │
├─────────────────────────────────────────────────────────────┤
│                    并发加速层 (Go)                          │
│               并行计算 / 网络通信 / 流式处理                 │
├─────────────────────────────────────────────────────────────┤
│                    安全包装层 (Rust)                         │
│               内存安全 / FFI绑定 / 错误处理                  │
├─────────────────────────────────────────────────────────────┤
│                    核心驱动层 (Zig)                          │
│               系统调用 / 硬件控制 / 编译时计算                │
├─────────────────────────────────────────────────────────────┤
│                 WASM/WASI 统一运行时                        │
│               字节码执行 / 跨平台兼容 / 沙箱安全              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 目录结构

```
UniCore/
├── src/
│   ├── core/
│   │   ├── isa/              # UniISA 统一指令集
│   │   ├── runtime/          # WASM运行时
│   │   ├── protocol/         # 协议层（契约/权限）
│   │   └── tools/            # 工具集（音视频/图像）
│   ├── lang/
│   │   ├── zig/              # Zig核心层
│   │   ├── rust/             # Rust安全层
│   │   ├── go/               # Go并发层
│   │   └── python/           # Python AI层
│   └── platform/
│       ├── android/          # Android打包
│       ├── esp32/            # ESP32固件
│       ├── windows/          # Windows程序
│       ├── mac/              # macOS程序
│       └── web/              # 网页版本
├── build/                     # 构建产物
└── dist/                     # 最终分发包
```

---

## 🚀 快速开始

### 网页版（直接打开）

```
src/platform/web/index.html
```

### Android APP 打包

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)
2. 导入 `src/platform/android/` 目录
3. 右键 → 发行 → 原生App-云打包 → Android

### ESP32 固件

需要安装：
- ESP-IDF
- Zig 编译器

```bash
cd src/platform/esp32
idf.py build
idf.py flash
```

### Windows/macOS 程序

```bash
# Windows
go build -o unicore.exe src/lang/go/...

# macOS
go build -o unicore src/lang/go/...
```

---

## 📋 UniISA 指令集

| 类别 | 指令 | 说明 |
|------|------|------|
| 计算 | `ADD`, `SUB`, `MUL`, `DIV` | 算术运算 |
| 逻辑 | `AND`, `OR`, `NOT`, `XOR` | 位运算 |
| 控制 | `JMP`, `JZ`, `CALL`, `RET` | 流程控制 |
| 内存 | `LOAD`, `STORE`, `ALLOC` | 内存操作 |
| 并行 | `SPAWN`, `SYNC`, `SEND` | 并发操作 |
| AI | `INFER`, `EMBED`, `ATTENTION` | AI推理 |

---

## 🛠️ 工具能力

| 工具 | 功能 |
|------|------|
| 音频 | 播放音频、语音识别、语音合成 |
| 图像 | 生成图像、图像处理、渲染 |
| 视频 | 视频捕获、编码、解码 |
| 控制 | 传感器读取、振动、位置 |
| 文件 | 文件读写、列表、删除 |
| 网络 | HTTP请求、WebSocket通信 |

---

## 📱 支持平台

| 平台 | 运行时 | 大小 |
|------|--------|------|
| Android | HBuilderX云打包 | ~5MB |
| ESP32 | wasm3-micro | ~50KB |
| Windows | Wasmtime | ~10MB |
| macOS | Wasmtime | ~10MB |
| Web | 原生WASM | 0KB |

---

## 🔧 开发指南

### 添加新的AI能力

编辑 `src/lang/python/ai_core.py`：

```python
class UniCoreAI:
    def new_capability(self, input_text):
        # 实现你的AI功能
        return {"result": "..."}
```

### 添加新的工具

编辑 `src/core/tools/tools.js`：

```javascript
class AudioTool {
    newTool(param) {
        // 实现你的工具
    }
}
```

### 定义新协议

编辑 `src/core/protocol/protocol.js`：

```javascript
class Contract {
    add_rule("new_permission", { max_calls: 10 });
}
```

---

## 📄 License

MIT License - 公共资源，自由使用

---

**UniCore - 让计算真正统一**
